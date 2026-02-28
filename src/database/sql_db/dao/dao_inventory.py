from ..entity.table_inventory import TableDataInventory
from ..conn import db

def get_inventory_list(page_current=1, page_size=10, filters=None):
    """
    分页查询，支持筛选
    :param filters: 字典，例如 {'project_name': 'ProjectA', 'function_name': 'FuncB'}
    """
    query = TableDataInventory.select()

    # 动态添加筛选条件
    if filters:
        if filters.get('project_name'):
            query = query.where(TableDataInventory.project_name == filters['project_name'])
        if filters.get('function_name'):
            query = query.where(TableDataInventory.function_name == filters['function_name'])

    total = query.count()
    
    # 分页与排序
    data_list = (query
                 .order_by(TableDataInventory.create_time.desc())
                 .paginate(page_current, page_size))
    
    return [d.__dict__['__data__'] for d in data_list], total

def batch_insert_inventory(data_list):
    """批量插入数据"""
    with db().atomic():
        TableDataInventory.insert_many(data_list).execute()

def get_filter_options():
    """获取所有已存在的项目名称和功能名称，供前端下拉框使用"""
    # 使用 distinct 去重查询
    projects = [p.project_name for p in TableDataInventory.select(TableDataInventory.project_name).distinct()]
    functions = [f.function_name for f in TableDataInventory.select(TableDataInventory.function_name).distinct()]
    return sorted(list(filter(None, projects))), sorted(list(filter(None, functions)))