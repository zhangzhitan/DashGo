from peewee import fn
from peewee import DoesNotExist, IntegrityError
from common.utilities.util_logger import Log
from ..conn import db
from ..entity.table_merchandise import Goods, PurchaseRecord, SalesOrder, DimIP, DimCharacter

logger = Log.get_logger(__name__)

def add_purchase_record(goods_id, buy_price, buy_count, channel, purchase_date):
    """进货：增加明细并更新库存"""
    database = db()
    with database.atomic() as txn:
        try:
            # 1. 插入进货记录
            PurchaseRecord.create(
                goods=goods_id,
                buy_price=buy_price,
                buy_count=buy_count,
                channel=channel,
                purchase_date=purchase_date
            )
            # 2. 更新商品主表总库存 (计算字段 stock_total 和 stock_for_sale)
            query = Goods.update(
                stock_total=Goods.stock_total + buy_count,
                stock_for_sale=Goods.stock_for_sale + buy_count
            ).where(Goods.goods_id == goods_id)
            query.execute()
        except Exception as e:
            logger.error(f"进货记录添加失败: {e}")
            txn.rollback()
            return False
        return True

def add_sales_order(goods_id, sale_price, sale_count, platform_order_no, shipping_address, sale_date):
    """出货：增加明细、计算利润并更新库存"""
    database = db()
    with database.atomic() as txn:
        try:
            # 1. 获取商品信息（用于计算利润，简单起见使用加权平均或最近购入价，此处演示直接扣减）
            goods = Goods.get_by_id(goods_id)
            
            # 2. 插入销售记录
            SalesOrder.create(
                goods=goods_id,
                sale_price=sale_price,
                sale_count=sale_count,
                platform_order_no=platform_order_no,
                shipping_address=shipping_address,
                sale_date=sale_date
            )
            
            # 3. 更新商品主表：减少库存，增加已售数量
            query = Goods.update(
                stock_total=Goods.stock_total - sale_count,
                stock_for_sale=Goods.stock_for_sale - sale_count,
                sold_count=Goods.sold_count + sale_count
            ).where(Goods.goods_id == goods_id)
            query.execute()
        except Exception as e:
            logger.error(f"出货记录添加失败: {e}")
            txn.rollback()
            return False
        return True

def get_inventory_summary():
    """获取看板数据：按IP统计盈利和库存"""
    query = (Goods
             .select(Goods.ip, 
                     fn.SUM(Goods.stock_total).alias('total_stock'),
                     fn.SUM(Goods.sold_count).alias('total_sold'))
             .group_by(Goods.ip))
    return list(query.dicts())
