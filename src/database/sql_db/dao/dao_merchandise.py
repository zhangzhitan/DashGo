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

# IP的增删改查

def get_all_ips():
    """获取所有IP，返回字典列表"""
    return list(DimIP.select().dicts())

def exists_ip_name(ip_name: str) -> bool:
    """检查IP是否已存在"""
    try:
        DimIP.get(DimIP.ip_name == ip_name)
        return True
    except DoesNotExist:
        return False

def create_ip(ip_name: str, ip_remark: str) -> bool:
    """新建IP"""
    database = db()
    with database.atomic() as txn:
        try:
            DimIP.create(ip_name=ip_name, ip_remark=ip_remark)
            txn.commit()
            return True
        except IntegrityError as e:
            logger.warning(f'创建IP {ip_name} 时出现异常: {e}', exc_info=True)
            txn.rollback()
            return False

def update_ip(old_ip_name: str, new_ip_name: str, ip_remark: str) -> bool:
    """更新IP信息 (注意：如果有外键关联，修改主键需要小心，通常建议主键不可改或级联更新)"""
    database = db()
    with database.atomic() as txn:
        try:
            ip = DimIP.get(DimIP.ip_name == old_ip_name)
            ip.ip_name = new_ip_name
            ip.ip_remark = ip_remark
            ip.save()
            txn.commit()
            return True
        except Exception as e:
            logger.warning(f'更新IP {old_ip_name} 时出现异常: {e}', exc_info=True)
            txn.rollback()
            return False

def delete_ip(ip_name: str) -> bool:
    """删除IP"""
    database = db()
    with database.atomic() as txn:
        try:
            DimIP.delete().where(DimIP.ip_name == ip_name).execute()
            txn.commit()
            return True
        except Exception as e:
            logger.warning(f'删除IP {ip_name} 时出现异常: {e}', exc_info=True)
            txn.rollback()
            return False

def batch_import_ips(records: list) -> tuple[bool, str]:
    """批量导入IP，遇到重复则忽略或更新，返回(是否成功, 提示信息)"""
    database = db()
    with database.atomic() as txn:
        try:
            # 简单粗暴的批量插入，如果ip_name是主键，可以使用 insert_many(...).on_conflict_replace() (Sqlite) 或 on_conflict_ignore() (Mysql)
            # 这里以遍历插入做示例，方便过滤错误数据
            success_count = 0
            for row in records:
                name = str(row.get('ip_name', '')).strip()
                if name and not exists_ip_name(name):
                    DimIP.create(ip_name=name, ip_remark=str(row.get('ip_remark', '')))
                    success_count += 1
            txn.commit()
            return True, f"成功导入 {success_count} 条新数据。"
        except Exception as e:
            logger.error(f"批量导入IP失败: {e}", exc_info=True)
            txn.rollback()
            return False, "导入失败，请检查数据格式。"