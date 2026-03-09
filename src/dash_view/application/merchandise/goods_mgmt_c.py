from server import app
from dash.dependencies import Input, Output, State
import dash
import pandas as pd
import io
import base64
from database.sql_db.dao import dao_goods
from dash_components import MessageManager
from dash import dcc 

def get_table_data():
    """获取表格最新数据并构造操作按钮"""
    return [
        {
            'key': str(item['goods_id']),
            'goods_id': item['goods_id'],
            'goods_name': item['goods_name'],
            'ip_name': item['ip_name'],
            'series_name': item['series_name'] or '',
            'character_name': item['character_name'] or '',
            'original_price': float(item['original_price']),
            'stock_self': item['stock_self'],
            'operation': [
                {'content': '编辑', 'type': 'primary', 'custom': f"update:{item['goods_id']}"},
                {'content': '删除', 'type': 'primary', 'custom': f"delete:{item['goods_id']}", 'danger': True}
            ]
        }
        for item in dao_goods.get_all_goods()
    ]

# --- 1. 拦截表格内按钮点击 (打开编辑/删除弹窗) ---
@app.callback(
    [
        Output('goods-delete-modal', 'visible'),
        Output('goods-delete-name', 'children'),
        Output('goods-delete-id-store', 'data'),
        
        Output('goods-edit-modal', 'visible'),
        Output('goods-edit-modal', 'title'),
        Output('goods-form-id', 'data'),
        Output('goods-form-name', 'value'),
        Output('goods-form-ip', 'value'),
        Output('goods-form-series', 'value'),
        Output('goods-form-char', 'value'),
        Output('goods-form-price', 'value'),
        Output('goods-form-stock', 'value'),
    ],
    Input('goods-mgmt-table', 'nClicksButton'),
    State('goods-mgmt-table', 'clickedCustom'),
    prevent_initial_call=True
)
def handle_table_btn_click(nClicksButton, clickedCustom: str):
    if not clickedCustom:
        return [dash.no_update] * 12
        
    action, goods_id_str = clickedCustom.split(':', 1)
    goods_id = int(goods_id_str)
    
    if action == 'delete':
        goods_info = next((i for i in dao_goods.get_all_goods() if i['goods_id'] == goods_id), None)
        return [True, goods_info['goods_name'], goods_id, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update]
        
    elif action == 'update':
        goods_info = next((i for i in dao_goods.get_all_goods() if i['goods_id'] == goods_id), None)
        return [dash.no_update, dash.no_update, dash.no_update, True, '编辑商品', goods_info['goods_id'], goods_info['goods_name'], goods_info['ip_name'], goods_info['series_name'] or '', goods_info['character_name'] or '', float(goods_info['original_price']), goods_info['stock_self']]

# --- 2. 打开新增弹窗 ---
@app.callback(
    [
        Output('goods-edit-modal', 'visible', allow_duplicate=True),
        Output('goods-edit-modal', 'title', allow_duplicate=True),
        Output('goods-form-id', 'data', allow_duplicate=True),
        Output('goods-form-name', 'value', allow_duplicate=True),
        Output('goods-form-ip', 'value', allow_duplicate=True),
        Output('goods-form-series', 'value', allow_duplicate=True),
        Output('goods-form-char', 'value', allow_duplicate=True),
        Output('goods-form-price', 'value', allow_duplicate=True),
        Output('goods-form-stock', 'value', allow_duplicate=True),
    ],
    Input('goods-btn-add', 'nClicks'),
    prevent_initial_call=True
)
def open_add_modal(nClicks):
    if not nClicks:
        return [dash.no_update] * 9
    return True, '新增商品', None, '', '', '', '', 0, 0

# --- 3. 提交表单 (新增或保存编辑) ---
@app.callback(
    [
        Output('goods-mgmt-table', 'data', allow_duplicate=True),
        Output('goods-edit-modal', 'visible', allow_duplicate=True)
    ],
    Input('goods-edit-modal', 'okCounts'),
    [
        State('goods-form-id', 'data'),
        State('goods-form-name', 'value'),
        State('goods-form-ip', 'value'),
        State('goods-form-series', 'value'),
        State('goods-form-char', 'value'),
        State('goods-form-price', 'value'),
        State('goods-form-stock', 'value')
    ],
    prevent_initial_call=True
)
def save_goods(okCounts, goods_id, name, ip_name, series_name, char_name, price, stock):
    if not name or not ip_name:
        MessageManager.warning('商品名称和所属IP不能为空')
        return dash.no_update, dash.no_update

    # 清理可能为空的字符串
    s_name = series_name.strip() if series_name else None
    c_name = char_name.strip() if char_name else None

    if goods_id: # 更新
        rt = dao_goods.update_goods(goods_id, name, ip_name, s_name, c_name, price, stock)
        msg = '商品更新'
    else: # 新增
        rt = dao_goods.create_goods(name, ip_name, s_name, c_name, price, stock)
        msg = '商品新增'

    if rt:
        MessageManager.success(f'{msg}成功（缺失维度已自动创建）')
        return get_table_data(), False
    else:
        MessageManager.error(f'{msg}失败，请检查系统日志')
        return dash.no_update, dash.no_update

# --- 4. 确认删除 ---
@app.callback(
    [
        Output('goods-mgmt-table', 'data', allow_duplicate=True),
        Output('goods-delete-modal', 'visible', allow_duplicate=True)
    ],
    Input('goods-delete-modal', 'okCounts'),
    State('goods-delete-id-store', 'data'),
    prevent_initial_call=True
)
def execute_delete(okCounts, goods_id):
    if dao_goods.delete_goods(goods_id):
        MessageManager.success('删除成功')
        return get_table_data(), False
    else:
        MessageManager.error('删除失败')
        return dash.no_update, dash.no_update

# --- 5. 导出 Excel ---
@app.callback(
    Output('goods-download-excel', 'data'),
    Input('goods-btn-export', 'nClicks'),
    prevent_initial_call=True
)
def export_excel(nClicks):
    if not nClicks:
        return dash.no_update
    data = dao_goods.get_all_goods()
    df = pd.DataFrame(data)
    # 丢弃 ID 列，并重命名
    df = df.drop(columns=['goods_id'], errors='ignore')
    df = df.rename(columns={
        'goods_name': '商品名称', 'ip_name': '所属IP', 
        'series_name': '所属系列', 'character_name': '所属角色',
        'original_price': '原价', 'stock_self': '自留库存'
    })
    return dcc.send_data_frame(df.to_excel, "商品数据导出.xlsx", index=False)

# --- 6. 导入 Excel ---
@app.callback(
    Output('goods-mgmt-table', 'data', allow_duplicate=True),
    Input('goods-upload-excel', 'contents'),
    prevent_initial_call=True
)
def import_excel(contents):
    if not contents:
        return dash.no_update
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        df = pd.read_excel(io.BytesIO(decoded))
        
        # 兼容中英文表头
        rename_map = {
            '商品名称': 'goods_name', '所属IP': 'ip_name', 
            '所属系列': 'series_name', '所属角色': 'character_name',
            '原价': 'original_price', '自留库存': 'stock_self'
        }
        df = df.rename(columns=rename_map)
        
        # 将 NaN 替换为空字符串或0，防止解析报错
        df = df.fillna({'series_name': '', 'character_name': '', 'original_price': 0, 'stock_self': 0})
        
        records = df.to_dict('records')
        success, msg = dao_goods.batch_import_goods(records)
        
        if success:
            MessageManager.success(msg)
            return get_table_data()
        else:
            MessageManager.error(msg)
            return dash.no_update
            
    except Exception as e:
        MessageManager.error(f'Excel 解析失败: {str(e)}')
        return dash.no_update