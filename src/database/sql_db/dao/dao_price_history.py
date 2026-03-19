# 文件：src/database/sql_db/dao/dao_price_history.py

from common.utilities.util_logger import Log
from ..entity.table_goods import GoodsPriceHistory, Goods

logger = Log.get_logger(__name__)

def get_all_price_history():
    """获取价格变更历史，【过滤】只显示销售中商品的数据"""
    query = (GoodsPriceHistory
             .select(GoodsPriceHistory) # 只取历史表的字段
             .join(Goods, on=(GoodsPriceHistory.goods_id == Goods.goods_id)) # 关联商品主表
             .where(Goods.sales_status == '销售中') # 仅过滤销售中状态
             .order_by(GoodsPriceHistory.change_time.desc())
             .dicts())
    return list(query)

def get_goods_options_for_trend():
    """获取用于前端下拉多选框的商品选项，【过滤】只显示销售中商品的数据"""
    query = (GoodsPriceHistory
             .select(GoodsPriceHistory.goods_id, GoodsPriceHistory.goods_name)
             .join(Goods, on=(GoodsPriceHistory.goods_id == Goods.goods_id)) # 关联商品主表
             .where(Goods.sales_status == '销售中') # 仅过滤销售中状态
             .distinct()
             .dicts())
    
    options = [{'label': f"{item['goods_name']} (ID:{item['goods_id']})", 'value': item['goods_id']} for item in query]
    return options

def get_price_history_by_goods_ids(goods_ids: list):
    """根据选择的商品IDs获取历史变更记录，同时确保商品状态是销售中"""
    if not goods_ids:
        return []
        
    query = (GoodsPriceHistory
             .select(GoodsPriceHistory.goods_id, GoodsPriceHistory.goods_name, GoodsPriceHistory.price, GoodsPriceHistory.change_time)
             .join(Goods, on=(GoodsPriceHistory.goods_id == Goods.goods_id)) # 关联商品主表
             .where(
                 (GoodsPriceHistory.goods_id.in_(goods_ids)) & 
                 (Goods.sales_status == '销售中') # 双重保险，防止被下架商品的脏ID传入
             )
             .order_by(GoodsPriceHistory.change_time.asc()) 
             .dicts())
    return list(query)