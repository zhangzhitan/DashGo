from server import app
from dash.dependencies import Input, Output, State
import dash
import pandas as pd
import feffery_antd_components as fac
from database.sql_db.dao import dao_inventory_status
from database.sql_db.dao import dao_sales 
from dash_components import MessageManager
from dash import dcc 

# --- 1. 级联筛选器逻辑 (复用) ---
@app.callback(
    [
        Output('inv-status-filter-series', 'options'),
        Output('inv-status-filter-char', 'options'),
        Output('inv-status-filter-series', 'value'),
        Output('inv-status-filter-char', 'value'),
    ],
    Input('inv-status-filter-ip', 'value'),
    prevent_initial_call=True
)
def update_filters(ip_v):
    if not ip_v:
        return [], [], None, None
    series_opts = dao_sales.get_series_options(ip_v)
    char_opts = dao_sales.get_char_options(ip_v)
    return series_opts, char_opts, None, None

# --- 2. 实时计算库存与渲染表格 ---
@app.callback(
    Output('inv-status-table', 'data'),
    [Input('inv-status-btn-search', 'nClicks')],
    [
        State('inv-status-filter-ip', 'value'),
        State('inv-status-filter-series', 'value'),
        State('inv-status-filter-char', 'value'),
    ],
    prevent_initial_call=False # 允许页面初始化时加载一次全量数据
)
def load_inventory_data(nClicks, ip_v, series_v, char_v):
    raw_data = dao_inventory_status.get_realtime_inventory(ip_v, series_v, char_v)
    
    formatted_data = []
    for row in raw_data:
        stock = row['current_stock']
        
        # 核心：前端标红预警
        if stock < 0:
            stock_display = fac.AntdText(f"{stock} (欠货)", type='danger', strong=True)
        elif stock == 0:
            stock_display = fac.AntdText(f"{stock} (售罄)", type='secondary')
        else:
            stock_display = fac.AntdText(str(stock), type='success', strong=True)
            
        formatted_data.append({
            'key': str(row['goods_id']),
            'goods_id': row['goods_id'],
            'ip_name': row['ip_name'],
            'series_name': row['series_name'],
            'character_name': row['character_name'],
            'goods_name': row['goods_name'],
            'total_buy': row['total_buy'],
            'total_sale': row['total_sale'],
            'current_stock': stock_display # 替换为带样式的组件
        })
        
    return formatted_data

# --- 3. 导出纯净版 Excel 数据 ---
@app.callback(
    Output('inv-status-download-excel', 'data'),
    Input('inv-status-btn-export', 'nClicks'),
    [
        State('inv-status-filter-ip', 'value'),
        State('inv-status-filter-series', 'value'),
        State('inv-status-filter-char', 'value'),
    ],
    prevent_initial_call=True
)
def export_excel(nClicks, ip_v, series_v, char_v):
    if not nClicks:
        return dash.no_update
        
    # 重新获取不带 HTML 标签的原始数据
    raw_data = dao_inventory_status.get_realtime_inventory(ip_v, series_v, char_v)
    if not raw_data:
        MessageManager.warning("暂无数据可导出")
        return dash.no_update
        
    df = pd.DataFrame(raw_data)
    df = df.rename(columns={
        'goods_id': '商品ID', 'ip_name': '所属IP', 
        'series_name': '所属系列', 'character_name': '所属角色',
        'goods_name': '商品名称', 'total_buy': '累计进货(件)', 
        'total_sale': '累计出货(件)', 'current_stock': '当前库存结余(件)'
    })
    
    # 调整导出列的顺序
    cols = ['商品ID', '所属IP', '所属系列', '所属角色', '商品名称', '累计进货(件)', '累计出货(件)', '当前库存结余(件)']
    df = df[cols]
    
    return dcc.send_data_frame(df.to_excel, "实时库存盘点表.xlsx", index=False)