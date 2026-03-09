from server import app
from dash.dependencies import Input, Output, State
import dash
import pandas as pd
import io
import base64
from database.sql_db.dao import dao_character
from dash_components import MessageManager
from dash import dcc 

def get_table_data():
    """获取表格最新数据并构造操作按钮"""
    return [
        {
            # 使用 IP || CharName 作为唯一标识和传参
            'key': f"{item['ip_name']}||{item['character_name']}",
            'ip_name': item['ip_name'],
            'character_name': item['character_name'],
            'character_remark': item['character_remark'],
            'operation': [
                {'content': '编辑', 'type': 'primary', 'custom': f"update:{item['ip_name']}||{item['character_name']}"},
                {'content': '删除', 'type': 'primary', 'custom': f"delete:{item['ip_name']}||{item['character_name']}", 'danger': True}
            ]
        }
        for item in dao_character.get_all_characters()
    ]

# --- 2. 拦截表格内按钮点击 (打开编辑/删除弹窗) ---
@app.callback(
    [
        Output('char-delete-modal', 'visible'),
        Output('char-delete-name', 'children'),
        Output('char-delete-ip-store', 'data'),
        
        Output('char-edit-modal', 'visible'),
        Output('char-edit-modal', 'title'),
        Output('char-form-ip', 'value'),
        Output('char-form-old-ip', 'data'),
        Output('char-form-name', 'value'),
        Output('char-form-old-name', 'data'),
        Output('char-form-remark', 'value'),
    ],
    Input('char-mgmt-table', 'nClicksButton'),
    State('char-mgmt-table', 'clickedCustom'),
    prevent_initial_call=True
)
def handle_table_btn_click(nClicksButton, clickedCustom: str):
    if not clickedCustom:
        return [dash.no_update] * 10
        
    action, payload = clickedCustom.split(':', 1)
    ip_name, char_name = payload.split('||', 1)
    
    if action == 'delete':
        display_name = f"【{ip_name}】的【{char_name}】"
        return [True, display_name, ip_name, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update]
        
    elif action == 'update':
        char_info = next((i for i in dao_character.get_all_characters() if i['ip_name'] == ip_name and i['character_name'] == char_name), None)
        return [dash.no_update, dash.no_update, dash.no_update, True, '编辑角色', char_info['ip_name'], char_info['ip_name'], char_info['character_name'], char_info['character_name'], char_info['character_remark']]

# --- 3. 打开新增弹窗 ---
@app.callback(
    [
        Output('char-edit-modal', 'visible', allow_duplicate=True),
        Output('char-edit-modal', 'title', allow_duplicate=True),
        Output('char-form-ip', 'value', allow_duplicate=True),
        Output('char-form-old-ip', 'data', allow_duplicate=True),
        Output('char-form-name', 'value', allow_duplicate=True),
        Output('char-form-old-name', 'data', allow_duplicate=True),
        Output('char-form-remark', 'value', allow_duplicate=True),
    ],
    Input('char-btn-add', 'nClicks'),
    prevent_initial_call=True
)
def open_add_modal(nClicks):
    if not nClicks:
        return [dash.no_update] * 7
    return True, '新增角色', '', None, '', None, ''

# --- 4. 提交表单 (新增或保存编辑) ---
@app.callback(
    [
        Output('char-mgmt-table', 'data', allow_duplicate=True),
        Output('char-edit-modal', 'visible', allow_duplicate=True)
    ],
    Input('char-edit-modal', 'okCounts'),
    [
        State('char-form-old-ip', 'data'),
        State('char-form-old-name', 'data'),
        State('char-form-ip', 'value'),
        State('char-form-name', 'value'),
        State('char-form-remark', 'value')
    ],
    prevent_initial_call=True
)
def save_character(okCounts, old_ip, old_name, new_ip, new_name, remark):
    if not new_ip or not new_name:
        MessageManager.warning('所属IP和角色名称不能为空')
        return dash.no_update, dash.no_update

    if old_ip and old_name: # 更新
        if (old_ip != new_ip or old_name != new_name) and dao_character.exists_character(new_ip, new_name):
            MessageManager.warning('修改后的角色在对应IP中已存在')
            return dash.no_update, dash.no_update
        rt = dao_character.update_character(old_ip, old_name, new_ip, new_name, remark)
        msg = '角色更新'
    else: # 新增
        if dao_character.exists_character(new_ip, new_name):
            MessageManager.warning('该角色在对应IP中已存在')
            return dash.no_update, dash.no_update
        rt = dao_character.create_character(new_ip, new_name, remark)
        msg = '角色新增'

    if rt:
        MessageManager.success(f'{msg}成功（若IP不存在已自动创建）')
        return get_table_data(), False
    else:
        MessageManager.error(f'{msg}失败，请检查系统日志')
        return dash.no_update, dash.no_update

# --- 5. 确认删除 ---
@app.callback(
    [
        Output('char-mgmt-table', 'data', allow_duplicate=True),
        Output('char-delete-modal', 'visible', allow_duplicate=True)
    ],
    Input('char-delete-modal', 'okCounts'),
    [
        State('char-delete-ip-store', 'data'),
        State('char-delete-name', 'children') # 这里包含拼接的文字，需要截取或从其他渠道拿名字
    ],
    prevent_initial_call=True
)
def execute_delete(okCounts, ip_name, display_text):
    # 从 【IP】的【NAME】中提取 name
    char_name = display_text.split('】的【')[1].replace('】', '')
    
    if dao_character.delete_character(ip_name, char_name):
        MessageManager.success('删除成功')
        return get_table_data(), False
    else:
        MessageManager.error('删除失败')
        return dash.no_update, dash.no_update

# --- 6. 导出 Excel ---
@app.callback(
    Output('char-download-excel', 'data'),
    Input('char-btn-export', 'nClicks'),
    prevent_initial_call=True
)
def export_excel(nClicks):
    if not nClicks:
        return dash.no_update
    data = dao_character.get_all_characters()
    df = pd.DataFrame(data)
    df = df.rename(columns={'ip_name': '所属IP', 'character_name': '角色名称', 'character_remark': '角色备注'})
    return dcc.send_data_frame(df.to_excel, "角色数据导出.xlsx", index=False)

# --- 7. 导入 Excel ---
@app.callback(
    Output('char-mgmt-table', 'data', allow_duplicate=True),
    Input('char-upload-excel', 'contents'),
    prevent_initial_call=True
)
def import_excel(contents):
    if not contents:
        return dash.no_update
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        df = pd.read_excel(io.BytesIO(decoded))
        # 兼容中文表头和英文表头
        if '所属IP' in df.columns:
            df = df.rename(columns={'所属IP': 'ip_name', '角色名称': 'character_name', '角色备注': 'character_remark'})
        
        records = df.to_dict('records')
        success, msg = dao_character.batch_import_characters(records)
        
        if success:
            MessageManager.success(msg)
            return get_table_data()
        else:
            MessageManager.error(msg)
            return dash.no_update
            
    except Exception as e:
        MessageManager.error(f'Excel 解析失败: {str(e)}')
        return dash.no_update