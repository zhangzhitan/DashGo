import datetime
from peewee import JOIN
from common.utilities.util_logger import Log
from ..conn import db
from ..entity.table_inventory import PurchaseOrder, PurchaseOrderDetail, DimChannel
from ..entity.table_goods import Goods

# 复用已写好的维度查询方法
from .dao_sales import get_ip_options, get_series_options, get_char_options, get_goods_options_filtered

logger = Log.get_logger(__name__)

def get_all_purchase_orders():
    query = (PurchaseOrder
             .select()
             .order_by(PurchaseOrder.order_date.desc())
             .dicts())
    return list(query)

def get_order_full_info(order_id: int):
    order = PurchaseOrder.get_by_id(order_id)
    order_dict = {
        'external_order_no': order.external_order_no,
        'channel_id': order.channel_id,
        'order_status': order.order_status,
        'remark': order.remark,
    }
    
    details_query = (PurchaseOrderDetail
                     .select(PurchaseOrderDetail, Goods.goods_name)
                     .join(Goods, on=(PurchaseOrderDetail.goods == Goods.goods_id))
                     .where(PurchaseOrderDetail.order_id == order_id)
                     .dicts())
    
    details_list = []
    for d in details_query:
        details_list.append({
            'key': str(d['goods']),
            'goods_id': d['goods'], 
            'goods_name': d['goods_name'],
            'price': float(d['buy_price']),
            'qty': d['buy_count'],
            'subtotal': float(d['subtotal'])
        })
    return order_dict, details_list

def save_purchase_order(order_id: int, external_no: str, channel_name: str, status: str, remark: str, items: list) -> tuple[bool, str]:
    database = db()
    with database.atomic() as txn:
        try:
            total_amount = sum(item['subtotal'] for item in items)
            channel, _ = DimChannel.get_or_create(channel_name=channel_name)
            
            if order_id: 
                order = PurchaseOrder.get_by_id(order_id)
                if order.external_order_no != external_no and PurchaseOrder.select().where(PurchaseOrder.external_order_no == external_no).exists():
                    return False, "外部单号已存在"
                
                order.external_order_no = external_no
                order.channel = channel
                order.order_status = status
                order.remark = remark
                order.total_amount = total_amount
                order.save()
                
                PurchaseOrderDetail.delete().where(PurchaseOrderDetail.order == order).execute()
            else: 
                if PurchaseOrder.select().where(PurchaseOrder.external_order_no == external_no).exists():
                    return False, "外部单号已存在"
                    
                order = PurchaseOrder.create(
                    external_order_no=external_no,
                    channel=channel,
                    order_status=status,
                    total_amount=total_amount,
                    remark=remark,
                    order_date=datetime.datetime.now()
                )
            
            detail_records = []
            for item in items:
                detail_records.append({
                    'order_id': order.order_id,
                    'goods_id': item['goods_id'],
                    'buy_price': item['price'],
                    'buy_count': item['qty'],
                    'subtotal': item['subtotal']
                })
            PurchaseOrderDetail.insert_many(detail_records).execute()
            
            txn.commit()
            return True, "保存成功"
        except Exception as e:
            logger.error(f'保存进货订单失败: {e}', exc_info=True)
            txn.rollback()
            return False, str(e)

def get_export_data():
    query = (PurchaseOrderDetail
             .select(
                 PurchaseOrder.external_order_no, PurchaseOrder.order_status,
                 PurchaseOrder.channel, PurchaseOrder.order_date,
                 PurchaseOrder.remark, Goods.goods_name,
                 PurchaseOrderDetail.buy_price, PurchaseOrderDetail.buy_count,
                 PurchaseOrderDetail.subtotal, PurchaseOrder.total_amount
             )
             .join(PurchaseOrder, on=(PurchaseOrderDetail.order == PurchaseOrder.order_id))
             .switch(PurchaseOrderDetail)
             .join(Goods, on=(PurchaseOrderDetail.goods == Goods.goods_id))
             .order_by(PurchaseOrder.order_date.desc())
             .dicts())
    return list(query)