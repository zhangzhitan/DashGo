from common.utilities.util_logger import Log
from ..entity.table_goods import GoodsPriceHistory, Goods

logger = Log.get_logger(__name__)

def get_all_price_history():
    """获取所有价格变更历史，按时间倒序排列 (用于表格展示)"""
    query = (GoodsPriceHistory
             .select()
             .order_by(GoodsPriceHistory.change_time.desc())
             .dicts())
    return list(query)

def get_goods_options_for_trend():
    """获取所有在历史表中出现过的商品，用于前端下拉多选框"""
    # 取出历史记录中去重后的 goods_id 和 goods_name
    query = (GoodsPriceHistory
             .select(GoodsPriceHistory.goods_id, GoodsPriceHistory.goods_name)
             .distinct()
             .dicts())
    
    # 转换为 fac.AntdSelect 兼容的格式: [{'label': '商品A', 'value': 1}, ...]
    options = [{'label': f"{item['goods_name']} (ID:{item['goods_id']})", 'value': item['goods_id']} for item in query]
    return options

def get_price_history_by_goods_ids(goods_ids: list):
    """根据选择的商品IDs，获取它们所有的历史变更记录（包含一个月前的数据以便做前向填充）"""
    if not goods_ids:
        return []
        
    query = (GoodsPriceHistory
             .select(GoodsPriceHistory.goods_id, GoodsPriceHistory.goods_name, GoodsPriceHistory.price, GoodsPriceHistory.change_time)
             .where(GoodsPriceHistory.goods_id.in_(goods_ids))
             .order_by(GoodsPriceHistory.change_time.asc()) # 按时间正序
             .dicts())
    return list(query)