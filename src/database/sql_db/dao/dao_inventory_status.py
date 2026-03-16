from peewee import fn, JOIN
from common.utilities.util_logger import Log
from ..entity.table_goods import Goods, DimIP, DimSeries, DimCharacter
from ..entity.table_inventory import PurchaseOrderDetail, SalesOrderDetail

logger = Log.get_logger(__name__)

def get_realtime_inventory(ip_name=None, series_name=None, char_name=None):
    """实时计算库存状态"""
    # 1. 查询基础商品信息
    goods_query = (Goods
                   .select(Goods.goods_id, Goods.goods_name, DimIP.ip_name, DimSeries.series_name, DimCharacter.character_name)
                   .join(DimIP, on=(Goods.ip == DimIP.ip_name)).switch(Goods)
                   .join(DimSeries, JOIN.LEFT_OUTER, on=(Goods.series == DimSeries.id)).switch(Goods)
                   .join(DimCharacter, JOIN.LEFT_OUTER, on=(Goods.character == DimCharacter.id))
                   .dicts())
    
    goods_list = list(goods_query)
    
    # 应用过滤条件
    if ip_name: goods_list = [g for g in goods_list if g['ip_name'] == ip_name]
    if series_name: goods_list = [g for g in goods_list if g['series_name'] == series_name]
    if char_name: goods_list = [g for g in goods_list if g['character_name'] == char_name]

    # 提取需要计算的商品ID列表
    goods_ids = [g['goods_id'] for g in goods_list]
    if not goods_ids:
        return []

    # 2. 批量聚合查询进货总数 (GROUP BY)
    buy_sums = (PurchaseOrderDetail
                .select(PurchaseOrderDetail.goods, fn.SUM(PurchaseOrderDetail.buy_count).alias('total_buy'))
                .where(PurchaseOrderDetail.goods.in_(goods_ids))
                .group_by(PurchaseOrderDetail.goods)
                .dicts())
    buy_map = {item['goods']: int(item['total_buy'] or 0) for item in buy_sums}

    # 3. 批量聚合查询出货总数 (GROUP BY)
    sale_sums = (SalesOrderDetail
                 .select(SalesOrderDetail.goods, fn.SUM(SalesOrderDetail.sale_count).alias('total_sale'))
                 .where(SalesOrderDetail.goods.in_(goods_ids))
                 .group_by(SalesOrderDetail.goods)
                 .dicts())
    sale_map = {item['goods']: int(item['total_sale'] or 0) for item in sale_sums}

    # 4. 在内存中进行计算与组装 (极速、安全)
    result = []
    for g in goods_list:
        gid = g['goods_id']
        t_buy = buy_map.get(gid, 0)
        t_sale = sale_map.get(gid, 0)
        current_stock = t_buy - t_sale
        
        result.append({
            'goods_id': gid,
            'goods_name': g['goods_name'],
            'ip_name': g['ip_name'],
            'series_name': g['series_name'] or '',
            'character_name': g['character_name'] or '',
            'total_buy': t_buy,
            'total_sale': t_sale,
            'current_stock': current_stock
        })
        
    return result