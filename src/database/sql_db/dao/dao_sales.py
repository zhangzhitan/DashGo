import datetime
from peewee import JOIN
from common.utilities.util_logger import Log
from ..conn import db
from ..entity.table_inventory import SalesOrder, SalesOrderDetail, DimChannel
from ..entity.table_goods import Goods, DimIP, DimSeries, DimCharacter

logger = Log.get_logger(__name__)

# --- 1. 原有基础查询 ---
def get_all_sales_orders():
    query = (SalesOrder
             .select()
             .order_by(SalesOrder.order_date.desc())
             .dicts())
    return list(query)

# --- 2. 新增：商品级联筛选支持 ---
def get_ip_options():
    return [{'label': ip.ip_name, 'value': ip.ip_name} for ip in DimIP.select()]

def get_series_options(ip_name: str):
    if not ip_name: return []
    return [{'label': s.series_name, 'value': s.series_name} for s in DimSeries.select().where(DimSeries.ip == ip_name)]

def get_char_options(ip_name: str):
    if not ip_name: return []
    return [{'label': c.character_name, 'value': c.character_name} for c in DimCharacter.select().where(DimCharacter.ip == ip_name)]

def get_goods_options_filtered(ip_name=None, series_name=None, char_name=None):
    """根据维度动态过滤商品，由于数据量不是天文数字，采用内存过滤以避免复杂的动态 JOIN 语法错误"""
    query = (Goods
             .select(Goods.goods_id, Goods.goods_name, DimIP.ip_name, DimSeries.series_name, DimCharacter.character_name)
             .join(DimIP, on=(Goods.ip == DimIP.ip_name)).switch(Goods)
             .join(DimSeries, JOIN.LEFT_OUTER, on=(Goods.series == DimSeries.id)).switch(Goods)
             .join(DimCharacter, JOIN.LEFT_OUTER, on=(Goods.character == DimCharacter.id))
             .dicts())
    
    res = list(query)
    if ip_name: res = [r for r in res if r['ip_name'] == ip_name]
    if series_name: res = [r for r in res if r['series_name'] == series_name]
    if char_name: res = [r for r in res if r['character_name'] == char_name]
    
    return [{'label': r['goods_name'], 'value': r['goods_id']} for r in res]

# --- 3. 新增：获取单个订单的完整信息（用于编辑回显） ---
def get_order_full_info(order_id: int):
    order = SalesOrder.get_by_id(order_id)
    order_dict = {
        'external_order_no': order.external_order_no,
        'channel_id': order.channel_id,
        'order_status': order.order_status,
        'shipping_address': order.shipping_address,
    }
    
    # 获取明细并格式化为前端 Store 需要的字典结构
    details_query = (SalesOrderDetail
                     .select(SalesOrderDetail, Goods.goods_name)
                     .join(Goods, on=(SalesOrderDetail.goods == Goods.goods_id))
                     .where(SalesOrderDetail.order_id == order_id)
                     .dicts())
    
    details_list = []
    for d in details_query:
        details_list.append({
            'key': str(d['goods']),
            'goods_id': d['goods'],
            'goods_name': d['goods_name'],
            'price': float(d['sale_price']),
            'qty': d['sale_count'],
            'subtotal': float(d['subtotal'])
        })
    return order_dict, details_list

# --- 4. 修改：保存或更新订单（融合） ---
def save_sales_order(order_id: int, external_no: str, channel_name: str, status: str, address: str, items: list) -> tuple[bool, str]:
    database = db()
    with database.atomic() as txn:
        try:
            total_amount = sum(item['subtotal'] for item in items)
            channel, _ = DimChannel.get_or_create(channel_name=channel_name)
            
            if order_id: # 更新逻辑
                order = SalesOrder.get_by_id(order_id)
                # 检查外部单号是否被其他订单占用
                if order.external_order_no != external_no and SalesOrder.select().where(SalesOrder.external_order_no == external_no).exists():
                    return False, "外部单号已存在"
                
                order.external_order_no = external_no
                order.channel = channel
                order.order_status = status
                order.shipping_address = address
                order.total_amount = total_amount
                order.save()
                
                # 删除旧明细，稍后全量插入新明细
                SalesOrderDetail.delete().where(SalesOrderDetail.order == order).execute()
            else: # 新增逻辑
                if SalesOrder.select().where(SalesOrder.external_order_no == external_no).exists():
                    return False, "外部单号已存在"
                    
                order = SalesOrder.create(
                    external_order_no=external_no,
                    channel=channel,
                    order_status=status,
                    total_amount=total_amount,
                    shipping_address=address,
                    order_date=datetime.datetime.now()
                )
            
            # 批量插入明细
            detail_records = []
            for item in items:
                detail_records.append({
                    'order_id': order.order_id,
                    'goods_id': item['goods_id'],
                    'sale_price': item['price'],
                    'sale_count': item['qty'],
                    'subtotal': item['subtotal']
                })
            SalesOrderDetail.insert_many(detail_records).execute()
            
            txn.commit()
            return True, "保存成功"
        except Exception as e:
            logger.error(f'保存出货订单失败: {e}', exc_info=True)
            txn.rollback()
            return False, str(e)

# --- 5. 新增：获取供导出的明细联表数据 ---
def get_export_data():
    query = (SalesOrderDetail
             .select(
                 SalesOrder.external_order_no, SalesOrder.order_status,
                 SalesOrder.channel, SalesOrder.order_date,
                 SalesOrder.shipping_address, Goods.goods_name,
                 SalesOrderDetail.sale_price, SalesOrderDetail.sale_count,
                 SalesOrderDetail.subtotal, SalesOrder.total_amount
             )
             .join(SalesOrder, on=(SalesOrderDetail.order == SalesOrder.order_id))
             .switch(SalesOrderDetail)
             .join(Goods, on=(SalesOrderDetail.goods == Goods.goods_id))
             .order_by(SalesOrder.order_date.desc())
             .dicts())
    return list(query)