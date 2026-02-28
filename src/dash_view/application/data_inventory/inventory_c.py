import base64
import io
import pandas as pd
from dash.dependencies import Input, Output, State
from dash import no_update
from server import app
from dash_components import MessageManager
from database.sql_db.dao import dao_inventory

# 1. 主查询回调：处理表格数据和分页
@app.callback(
    [Output('inventory-table', 'data'),
     Output('inventory-table', 'pagination'),
     # 同时更新筛选器的选项，确保新导入的数据能被筛选到
     Output('inventory-filter-project', 'options'),
     Output('inventory-filter-function', 'options')],
    [Input('inventory-table', 'pagination'),
     Input('inventory-btn-search', 'nClicks'), # 点击查询按钮触发
     Input('inventory-upload', 'contents')],   # 上传成功也触发刷新
    [State('inventory-filter-project', 'value'),
     State('inventory-filter-function', 'value')],
    prevent_initial_call=False
)
def update_view(pagination, n_clicks, upload_contents, project_val, function_val):
    # 获取分页参数
    current = pagination.get('current', 1)
    page_size = pagination.get('pageSize', 10)
    
    # 构建筛选条件
    filters = {}
    if project_val:
        filters['project_name'] = project_val
    if function_val:
        filters['function_name'] = function_val

    # 查询数据
    data_list, total = dao_inventory.get_inventory_list(current, page_size, filters)
    
    # 更新分页总数
    pagination['total'] = total

    # 获取最新的筛选选项（可选：也可以单独开一个回调优化性能）
    proj_opts, func_opts = dao_inventory.get_filter_options()
    
    return data_list, pagination, proj_opts, func_opts


# 2. Excel 上传回调
@app.callback(
    Output('global-message-container', 'children', allow_duplicate=True),
    Input('inventory-upload', 'contents'),
    prevent_initial_call=True
)
def upload_file(contents):
    if contents is None:
        return no_update

    _, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        df = pd.read_excel(io.BytesIO(decoded))
        
        # 定义 Excel 列名到数据库字段的映射
        # 键是 Excel 表头，值是 Peewee 模型字段名
        column_map = {
            '数据集名称': 'dataset_name',
            '项目名称': 'project_name',
            '详细数据项': 'detailed_data', # e.g. "VIN, 排放量"
            '简要描述': 'short_description',
            '功能名称': 'function_name',
            '数据主体': 'data_subject',
            '业务最小化要求': 'requirement_type',
            '估计数据主体数量': 'subject_amount',
            '特殊类别的个人数据': 'sensitive_category',
            '收集来源': 'collection_source',
            '收集时间': 'collection_time_desc'
        }

        # 简单的必填列校验
        missing_cols = [col for col in column_map.keys() if col not in df.columns]
        if missing_cols:
            return MessageManager.error(content=f'上传失败：Excel 缺少列: {", ".join(missing_cols)}')

        # 构造插入数据
        insert_data = []
        for _, row in df.iterrows():
            # 简单的数据清洗
            row_data = {}
            for xls_col, db_col in column_map.items():
                val = row.get(xls_col)
                # 处理空值和类型
                if pd.isna(val):
                    val = None
                else:
                    val = str(val).strip() # 默认转字符串处理
                
                # 特殊处理：数量字段转整数
                if db_col == 'subject_amount':
                    try:
                        val = int(float(val)) if val else 0
                    except:
                        val = 0
                
                row_data[db_col] = val
            
            row_data['create_by'] = 'admin' # 暂时硬编码，实际可用 session
            insert_data.append(row_data)

        dao_inventory.batch_insert_inventory(insert_data)
        
        return MessageManager.success(content=f'成功导入 {len(insert_data)} 条数据')

    except Exception as e:
        return MessageManager.error(content=f'解析文件出错: {str(e)}')