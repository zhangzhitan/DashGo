from peewee import JOIN, DoesNotExist, IntegrityError
from common.utilities.util_logger import Log
from ..conn import db
from ..entity.table_goods import DimIP, DimSeries, DimCharacter, Goods, GoodsPriceHistory

logger = Log.get_logger(__name__)

def get_all_goods():
    """获取所有商品，包含关联的维度名称，返回字典列表"""
    # 由于系列和角色可以为 null，这里必须使用 LEFT OUTER JOIN
    query = (Goods
             .select(
                 Goods.goods_id,
                 Goods.goods_name,
                 Goods.original_price,
                 Goods.stock_self,
                 DimIP.ip_name,
                 DimSeries.series_name,
                 DimCharacter.character_name
             )
             .join(DimIP, on=(Goods.ip == DimIP.ip_name))
             .switch(Goods)
             .join(DimSeries, JOIN.LEFT_OUTER, on=(Goods.series == DimSeries.id))
             .switch(Goods)
             .join(DimCharacter, JOIN.LEFT_OUTER, on=(Goods.character == DimCharacter.id))
             .order_by(Goods.goods_id.desc())
             .dicts())
    return list(query)

def _ensure_dimensions(ip_name: str, series_name: str = None, character_name: str = None):
    """【核心扩展】确保关联的维度存在，不存在则自动创建"""
    if not ip_name:
        return None, None, None
        
    ip, _ = DimIP.get_or_create(ip_name=ip_name, defaults={'ip_remark': '创建商品时自动补充'})
    
    series_obj = None
    if series_name:
        series_obj, _ = DimSeries.get_or_create(ip=ip, series_name=series_name, defaults={'series_batch': '', 'series_remark': '创建商品时自动补充'})
        
    char_obj = None
    if character_name:
        char_obj, _ = DimCharacter.get_or_create(ip=ip, character_name=character_name, defaults={'character_remark': '创建商品时自动补充'})
        
    return ip, series_obj, char_obj

def create_goods(goods_name: str, ip_name: str, series_name: str, character_name: str, original_price: float, stock_self: int) -> bool:
    """新建商品（自动补充缺失的维度）"""
    database = db()
    with database.atomic() as txn:
        try:
            ip, series_obj, char_obj = _ensure_dimensions(ip_name, series_name, character_name)
            # 获取创建后的商品对象，以拿到自增的 goods_id
            goods = Goods.create(
                goods_name=goods_name,
                ip=ip,
                series=series_obj,
                character=char_obj,
                original_price=original_price or 0.0,
                stock_self=stock_self or 0
            )
            
            # 【新增埋点】记录价格
            GoodsPriceHistory.create(
                goods_id=goods.goods_id, goods_name=goods_name, 
                price=original_price or 0.0, change_type='新增'
            )
            
            txn.commit()
            return True
        except Exception as e:
            logger.warning(f'创建商品 {goods_name} 时出现异常: {e}', exc_info=True)
            txn.rollback()
            return False

def update_goods(goods_id: int, goods_name: str, ip_name: str, series_name: str, character_name: str, original_price: float, stock_self: int) -> bool:
    """更新商品信息（自动补充缺失的维度）"""
    database = db()
    with database.atomic() as txn:
        try:
            ip, series_obj, char_obj = _ensure_dimensions(ip_name, series_name, character_name)
            goods = Goods.get(Goods.goods_id == goods_id)
            
            # 判断价格是否发生了变化，如果变化则记录
            if float(goods.original_price) != float(original_price or 0.0):
                GoodsPriceHistory.create(
                    goods_id=goods_id, goods_name=goods_name, 
                    price=original_price or 0.0, change_type='价格修改'
                )
            elif goods.goods_name != goods_name:
                # 即使价格没变，但如果名字变了，也可以选择记录一条以便追踪溯源
                GoodsPriceHistory.create(
                    goods_id=goods_id, goods_name=goods_name, 
                    price=original_price or 0.0, change_type='名称修改'
                )
            
            # --- 修复部分：必须显式更新所有字段 ---
            goods.goods_name = goods_name
            goods.ip = ip
            goods.series = series_obj
            goods.character = char_obj
            goods.original_price = original_price or 0.0
            goods.stock_self = stock_self or 0
            # ------------------------------------
            
            goods.save()
            txn.commit()
            return True
        except Exception as e:
            logger.warning(f'更新商品 ID:{goods_id} 时出现异常: {e}', exc_info=True)
            txn.rollback()
            return False

def delete_goods(goods_id: int) -> bool:
    """删除商品"""
    database = db()
    with database.atomic() as txn:
        try:
            # 【新增埋点】在删除前先查询出商品信息用于记录
            goods = Goods.get(Goods.goods_id == goods_id)
            GoodsPriceHistory.create(
                goods_id=goods_id, goods_name=goods.goods_name, 
                price=goods.original_price, change_type='删除'
            )
            
            Goods.delete().where(Goods.goods_id == goods_id).execute()
            txn.commit()
            return True
        except Exception as e:
            logger.warning(f'删除商品 ID:{goods_id} 时出现异常: {e}', exc_info=True)
            txn.rollback()
            return False

def batch_import_goods(records: list) -> tuple[bool, str]:
    """批量导入商品（自动补充缺失的维度）"""
    database = db()
    with database.atomic() as txn:
        try:
            success_count = 0
            history_list = [] # 用于批量插入历史记录
            
            for row in records:
                # ... 之前解析字段的逻辑保持不变 ...
                
                ip, series_obj, char_obj = _ensure_dimensions(ip_n, sn, cn)
                goods = Goods.create(
                    goods_name=gn, ip=ip, series=series_obj,
                    character=char_obj, original_price=op, stock_self=st
                )
                
                # 【新增埋点】追加到历史记录列表
                history_list.append({
                    'goods_id': goods.goods_id,
                    'goods_name': gn,
                    'price': op,
                    'change_type': '导入新增',
                    'change_time': datetime.datetime.now()
                })
                success_count += 1
                
            # 批量插入历史记录提升性能
            if history_list:
                GoodsPriceHistory.insert_many(history_list).execute()
                
            txn.commit()
            return True, f"成功导入 {success_count} 条商品数据..."
        except Exception as e:
            logger.error(f"批量导入商品失败: {e}", exc_info=True)
            txn.rollback()
            return False, f"导入失败: {str(e)}"