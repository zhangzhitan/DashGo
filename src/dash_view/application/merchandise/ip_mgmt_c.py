from server import app
from dash.dependencies import Input, Output, State
import dash
import pandas as pd
import io
import base64
from database.sql_db.dao import dao_goods_ip
from dash_components import MessageManager
from i18n import t__default
from dash import dcc 

def get_table_data():
    """获取表格最新数据并构造操作按钮"""
    return [
        {
            'key': item['ip_name'],
            'ip_name': item['ip_name'],
            'ip_remark': item['ip_remark'],
            'operation': [
                {'content': '编辑', 'type': 'primary', 'custom': 'update:' + item['ip_name']},
                {'content': '删除', 'type': 'primary', 'custom': 'delete:' + item['ip_name'], 'danger': True}
            ]
        }
        for item in dao_goods_ip.get_all_ips()
    ]

# # --- 1. 初始化与刷新表格 ---
# @app.callback(
#     Output('ip-mgmt-table', 'data'),
#     Input('ip-mgmt-table', 'id')
# )
# def load_table(_):
#     return get_table_data()

# --- 2. 拦截表格内按钮点击 (打开编辑/删除弹窗) ---
@app.callback(
    [
        Output('ip-delete-modal', 'visible'),
        Output('ip-delete-name', 'children'),
        Output('ip-edit-modal', 'visible'),
        Output('ip-edit-modal', 'title'),
        Output('ip-form-name', 'value'),
        Output('ip-form-old-name', 'data'),
        Output('ip-form-remark', 'value'),
    ],
    Input('ip-mgmt-table', 'nClicksButton'),
    State('ip-mgmt-table', 'clickedCustom'),
    prevent_initial_call=True
)
def handle_table_btn_click(nClicksButton, clickedCustom: str):
    if not clickedCustom:
        return [dash.no_update] * 7
        
    action, ip_name = clickedCustom.split(':', 1)
    
    if action == 'delete':
        return [True, ip_name, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update]
        
    elif action == 'update':
        ip_info = next((i for i in dao_goods_ip.get_all_ips() if i['ip_name'] == ip_name), None)
        return [dash.no_update, dash.no_update, True, '编辑 IP', ip_info['ip_name'], ip_info['ip_name'], ip_info['ip_remark']]

# --- 3. 打开新增弹窗 ---
@app.callback(
    [
        Output('ip-edit-modal', 'visible', allow_duplicate=True),
        Output('ip-edit-modal', 'title', allow_duplicate=True),
        Output('ip-form-name', 'value', allow_duplicate=True),
        Output('ip-form-old-name', 'data', allow_duplicate=True),
        Output('ip-form-remark', 'value', allow_duplicate=True),
    ],
    Input('ip-btn-add', 'nClicks'),
    prevent_initial_call=True
)
def open_add_modal(nClicks):
    # 【修复】拦截 nClicks 为空的情况，防止静默阻断
    if not nClicks:
        return [dash.no_update] * 5
    # 打开弹窗，重置表单内容
    return True, '新增 IP', '', None, ''

# --- 4. 提交表单 (新增或保存编辑) ---
@app.callback(
    [
        Output('ip-mgmt-table', 'data', allow_duplicate=True),
        Output('ip-edit-modal', 'visible', allow_duplicate=True) # 【修复】保存后必须关闭弹窗
    ],
    Input('ip-edit-modal', 'okCounts'),
    [
        State('ip-form-old-name', 'data'),
        State('ip-form-name', 'value'),
        State('ip-form-remark', 'value')
    ],
    prevent_initial_call=True
)
def save_ip(okCounts, old_name, new_name, remark):
    if not new_name:
        MessageManager.warning('IP名称不能为空')
        return dash.no_update, dash.no_update

    if old_name: # 更新
        if old_name != new_name and dao_goods_ip.exists_ip_name(new_name):
            MessageManager.warning('修改后的IP名称已存在')
            return dash.no_update, dash.no_update
        rt = dao_goods_ip.update_ip(old_name, new_name, remark)
        msg = 'IP更新'
    else: # 新增
        if dao_goods_ip.exists_ip_name(new_name):
            MessageManager.warning('该IP名称已存在')
            return dash.no_update, dash.no_update
        rt = dao_goods_ip.create_ip(new_name, remark)
        msg = 'IP新增'

    if rt:
        MessageManager.success(f'{msg}成功')
        # 【修复】返回刷新后的数据，并返回 False 关闭弹窗
        return get_table_data(), False
    else:
        MessageManager.error(f'{msg}失败，请检查系统日志')
        return dash.no_update, dash.no_update

# --- 5. 确认删除 ---
@app.callback(
    [
        Output('ip-mgmt-table', 'data', allow_duplicate=True),
        Output('ip-delete-modal', 'visible', allow_duplicate=True) # 【修复】删除后也需要关闭二次确认弹窗
    ],
    Input('ip-delete-modal', 'okCounts'),
    State('ip-delete-name', 'children'),
    prevent_initial_call=True
)
def execute_delete(okCounts, ip_name):
    if dao_goods_ip.delete_ip(ip_name):
        MessageManager.success('删除成功')
        return get_table_data(), False
    else:
        MessageManager.error('删除失败，可能有关联的商品数据')
        return dash.no_update, dash.no_update

# --- 6. 导出 Excel ---
@app.callback(
    Output('ip-download-excel', 'data'),
    Input('ip-btn-export', 'nClicks'),
    prevent_initial_call=True
)
def export_excel(nClicks):
    if not nClicks:
        return dash.no_update
    data = dao_goods_ip.get_all_ips()
    df = pd.DataFrame(data)
    df = df.rename(columns={'ip_name': 'IP名称', 'ip_remark': '备注'})
    return dcc.send_data_frame(df.to_excel, "IP数据导出.xlsx", index=False)

# --- 7. 导入 Excel ---
@app.callback(
    Output('ip-mgmt-table', 'data', allow_duplicate=True),
    Input('ip-upload-excel', 'contents'),
    prevent_initial_call=True
)
def import_excel(contents):
    if not contents:
        return dash.no_update
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        df = pd.read_excel(io.BytesIO(decoded))
        df = df.rename(columns={'IP名称': 'ip_name', '备注': 'ip_remark'})
        records = df.to_dict('records')
        
        success, msg = dao_goods_ip.batch_import_ips(records)
        if success:
            MessageManager.success(msg)
            return get_table_data()
        else:
            MessageManager.error(msg)
            return dash.no_update
            
    except Exception as e:
        MessageManager.error(f'Excel 解析失败: {str(e)}')
        return dash.no_update