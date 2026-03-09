from server import app
from dash.dependencies import Input, Output, State
import dash
import pandas as pd
import io
import base64
from database.sql_db.dao import dao_series
from dash_components import MessageManager
from dash import dcc 

def get_table_data():
    """获取表格最新数据并构造操作按钮"""
    return [
        {
            # 使用 IP || SeriesName 作为唯一标识
            'key': f"{item['ip_name']}||{item['series_name']}",
            'ip_name': item['ip_name'],
            'series_name': item['series_name'],
            'series_batch': item['series_batch'],
            'series_remark': item['series_remark'],
            'operation': [
                {'content': '编辑', 'type': 'primary', 'custom': f"update:{item['ip_name']}||{item['series_name']}"},
                {'content': '删除', 'type': 'primary', 'custom': f"delete:{item['ip_name']}||{item['series_name']}", 'danger': True}
            ]
        }
        for item in dao_series.get_all_series()
    ]

# --- 1. 拦截表格内按钮点击 (打开编辑/删除弹窗) ---
@app.callback(
    [
        Output('series-delete-modal', 'visible'),
        Output('series-delete-name', 'children'),
        Output('series-delete-ip-store', 'data'),
        
        Output('series-edit-modal', 'visible'),
        Output('series-edit-modal', 'title'),
        Output('series-form-ip', 'value'),
        Output('series-form-old-ip', 'data'),
        Output('series-form-name', 'value'),
        Output('series-form-old-name', 'data'),
        Output('series-form-batch', 'value'),
        Output('series-form-remark', 'value'),
    ],
    Input('series-mgmt-table', 'nClicksButton'),
    State('series-mgmt-table', 'clickedCustom'),
    prevent_initial_call=True
)
def handle_table_btn_click(nClicksButton, clickedCustom: str):
    if not clickedCustom:
        return [dash.no_update] * 11
        
    action, payload = clickedCustom.split(':', 1)
    ip_name, series_name = payload.split('||', 1)
    
    if action == 'delete':
        display_name = f"【{ip_name}】的【{series_name}】"
        return [True, display_name, ip_name, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update]
        
    elif action == 'update':
        series_info = next((i for i in dao_series.get_all_series() if i['ip_name'] == ip_name and i['series_name'] == series_name), None)
        return [dash.no_update, dash.no_update, dash.no_update, True, '编辑系列', series_info['ip_name'], series_info['ip_name'], series_info['series_name'], series_info['series_name'], series_info['series_batch'], series_info['series_remark']]

# --- 2. 打开新增弹窗 ---
@app.callback(
    [
        Output('series-edit-modal', 'visible', allow_duplicate=True),
        Output('series-edit-modal', 'title', allow_duplicate=True),
        Output('series-form-ip', 'value', allow_duplicate=True),
        Output('series-form-old-ip', 'data', allow_duplicate=True),
        Output('series-form-name', 'value', allow_duplicate=True),
        Output('series-form-old-name', 'data', allow_duplicate=True),
        Output('series-form-batch', 'value', allow_duplicate=True),
        Output('series-form-remark', 'value', allow_duplicate=True),
    ],
    Input('series-btn-add', 'nClicks'),
    prevent_initial_call=True
)
def open_add_modal(nClicks):
    if not nClicks:
        return [dash.no_update] * 8
    return True, '新增系列', '', None, '', None, '', ''

# --- 3. 提交表单 (新增或保存编辑) ---
@app.callback(
    [
        Output('series-mgmt-table', 'data', allow_duplicate=True),
        Output('series-edit-modal', 'visible', allow_duplicate=True)
    ],
    Input('series-edit-modal', 'okCounts'),
    [
        State('series-form-old-ip', 'data'),
        State('series-form-old-name', 'data'),
        State('series-form-ip', 'value'),
        State('series-form-name', 'value'),
        State('series-form-batch', 'value'),
        State('series-form-remark', 'value')
    ],
    prevent_initial_call=True
)
def save_series(okCounts, old_ip, old_name, new_ip, new_name, batch, remark):
    if not new_ip or not new_name:
        MessageManager.warning('所属IP和系列名称不能为空')
        return dash.no_update, dash.no_update

    if old_ip and old_name: # 更新
        if (old_ip != new_ip or old_name != new_name) and dao_series.exists_series(new_ip, new_name):
            MessageManager.warning('修改后的系列在对应IP中已存在')
            return dash.no_update, dash.no_update
        rt = dao_series.update_series(old_ip, old_name, new_ip, new_name, str(batch or ''), remark)
        msg = '系列更新'
    else: # 新增
        if dao_series.exists_series(new_ip, new_name):
            MessageManager.warning('该系列在对应IP中已存在')
            return dash.no_update, dash.no_update
        rt = dao_series.create_series(new_ip, new_name, str(batch or ''), remark)
        msg = '系列新增'

    if rt:
        MessageManager.success(f'{msg}成功（若IP不存在已自动创建）')
        return get_table_data(), False
    else:
        MessageManager.error(f'{msg}失败，请检查系统日志')
        return dash.no_update, dash.no_update

# --- 4. 确认删除 ---
@app.callback(
    [
        Output('series-mgmt-table', 'data', allow_duplicate=True),
        Output('series-delete-modal', 'visible', allow_duplicate=True)
    ],
    Input('series-delete-modal', 'okCounts'),
    [
        State('series-delete-ip-store', 'data'),
        State('series-delete-name', 'children') 
    ],
    prevent_initial_call=True
)
def execute_delete(okCounts, ip_name, display_text):
    series_name = display_text.split('】的【')[1].replace('】', '')
    
    if dao_series.delete_series(ip_name, series_name):
        MessageManager.success('删除成功')
        return get_table_data(), False
    else:
        MessageManager.error('删除失败')
        return dash.no_update, dash.no_update

# --- 5. 导出 Excel ---
@app.callback(
    Output('series-download-excel', 'data'),
    Input('series-btn-export', 'nClicks'),
    prevent_initial_call=True
)
def export_excel(nClicks):
    if not nClicks:
        return dash.no_update
    data = dao_series.get_all_series()
    df = pd.DataFrame(data)
    df = df.rename(columns={'ip_name': '所属IP', 'series_name': '系列名称', 'series_batch': '系列批次', 'series_remark': '备注'})
    return dcc.send_data_frame(df.to_excel, "系列数据导出.xlsx", index=False)

# --- 6. 导入 Excel ---
@app.callback(
    Output('series-mgmt-table', 'data', allow_duplicate=True),
    Input('series-upload-excel', 'contents'),
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
        if '所属IP' in df.columns:
            df = df.rename(columns={'所属IP': 'ip_name', '系列名称': 'series_name', '系列批次': 'series_batch', '备注': 'series_remark'})
        
        records = df.to_dict('records')
        success, msg = dao_series.batch_import_series(records)
        
        if success:
            MessageManager.success(msg)
            return get_table_data()
        else:
            MessageManager.error(msg)
            return dash.no_update
            
    except Exception as e:
        MessageManager.error(f'Excel 解析失败: {str(e)}')
        return dash.no_update