from common.utilities.util_logger import Log
from ..entity.table_goods import GoodsPriceHistory

logger = Log.get_logger(__name__)

def get_all_price_history():
    """获取所有价格变更历史，按时间倒序排列"""
    query = (GoodsPriceHistory
             .select()
             .order_by(GoodsPriceHistory.change_time.desc())
             .dicts())
    return list(query)