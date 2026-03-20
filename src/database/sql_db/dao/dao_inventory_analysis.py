# src/database/sql_db/dao/dao_inventory_analysis.py
import datetime
from peewee import fn, JOIN
from ..conn import db
from ..entity.table_inventory import InventoryDailySnapshot, PurchaseOrderDetail, SalesOrderDetail
from ..entity.table_goods import Goods, DimIP, DimSeries, DimCharacter

# ================= 1. 供定时任务调用的写入逻辑 =================
def generate_snapshot_for_date(target_date: datetime.date):
    """
    计算指定日期的进销存快照并入库 (通常在凌晨执行, 传入昨天的日期)
    """
    database = db()
    with database.atomic():
        # 获取所有商品的基础字典
        goods_list = list(Goods.select(Goods.goods_id))
        
        # 1. 查当天的入库量
        in_query = (PurchaseOrderDetail
                    .select(PurchaseOrderDetail.goods, fn.SUM(PurchaseOrderDetail.buy_count).alias('total_in'))
                    .join(PurchaseOrderDetail.order) # 假设需要关联订单表查日期
                    .where(fn.DATE(PurchaseOrderDetail.order.order_date) == target_date)
                    .group_by(PurchaseOrderDetail.goods).dicts())
        in_map = {item['goods']: item['total_in'] for item in in_query}

        # 2. 查当天的出库量
        out_query = (SalesOrderDetail
                     .select(SalesOrderDetail.goods, fn.SUM(SalesOrderDetail.sale_count).alias('total_out'))
                     .join(SalesOrderDetail.order)
                     .where(fn.DATE(SalesOrderDetail.order.order_date) == target_date)
                     .group_by(SalesOrderDetail.goods).dicts())
        out_map = {item['goods']: item['total_out'] for item in out_query}

        # 3. 查昨天的结余库存 (如果 target_date 是今天，则查昨天)
        prev_date = target_date - datetime.timedelta(days=1)
        prev_stock_query = (InventoryDailySnapshot
                            .select(InventoryDailySnapshot.goods, InventoryDailySnapshot.stock_qty)
                            .where(InventoryDailySnapshot.snapshot_date == prev_date).dicts())
        prev_stock_map = {item['goods']: item['stock_qty'] for item in prev_stock_query}

        # 4. 计算并全量保存今天的快照
        snapshot_records = []
        for g in goods_list:
            gid = g.goods_id
            in_q = in_map.get(gid, 0)
            out_q = out_map.get(gid, 0)
            prev_s = prev_stock_map.get(gid, 0)
            
            # 今日结余 = 昨日结余 + 今日入库 - 今日出库
            current_stock = prev_s + in_q - out_q
            
            # 哪怕今天没交易，也要继承昨日库存，以保证图表曲线不中断
            if in_q > 0 or out_q > 0 or current_stock != 0:
                snapshot_records.append({
                    'snapshot_date': target_date,
                    'goods_id': gid,
                    'in_qty': in_q,
                    'out_qty': out_q,
                    'stock_qty': current_stock
                })
        
        if snapshot_records:
            # 批量插入/更新 (使用 MySQL 的 on_conflict_ignore 或 replace)
            InventoryDailySnapshot.insert_many(snapshot_records).on_conflict_replace().execute()

# ================= 2. 供前端图表查询的逻辑 =================
def get_analysis_chart_data(start_date: str, end_date: str, ip_name=None, series_id=None, char_id=None):
    """
    按日期分组聚合图表数据
    """
    query = (InventoryDailySnapshot
             .select(
                 InventoryDailySnapshot.snapshot_date,
                 fn.SUM(InventoryDailySnapshot.in_qty).alias('sum_in'),
                 fn.SUM(InventoryDailySnapshot.out_qty).alias('sum_out'),
                 fn.SUM(InventoryDailySnapshot.stock_qty).alias('sum_stock')
             )
             .join(Goods, on=(InventoryDailySnapshot.goods == Goods.goods_id))
             .where(
                 (InventoryDailySnapshot.snapshot_date >= start_date) & 
                 (InventoryDailySnapshot.snapshot_date <= end_date)
             ))
    
    # 动态追加商品维度过滤
    if ip_name:
        query = query.where(Goods.ip == ip_name)
    if series_id:
        query = query.where(Goods.series == series_id)
    if char_id:
        query = query.where(Goods.character == char_id)
        
    query = query.group_by(InventoryDailySnapshot.snapshot_date).order_by(InventoryDailySnapshot.snapshot_date.asc())
    
    return list(query.dicts())