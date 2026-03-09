from server import app
from dash.dependencies import Input, Output
import dash
import pandas as pd
from database.sql_db.dao import dao_price_history
from dash import dcc 

def get_table_data():
    """获取表格最新数据并格式化时间"""
    records = dao_price_history.get_all_price_history()
    formatted_data = []
    for item in records:
        formatted_data.append({
            'key': str(item['history_id']),
            'goods_id': item['goods_id'],
            'goods_name': item['goods_name'],
            'price': float(item['price']),
            'change_type': fac.AntdTag(content=item['change_type'], color='blue' if '新增' in item['change_type'] else ('red' if '删除' in item['change_type'] else 'orange')), # 给变更类型加个标签样式，使其更直观
            'change_time': item['change_time'].strftime('%Y-%m-%d %H:%M:%S') if item['change_time'] else ''
        })
    return formatted_data

# --- 1. 导出 Excel ---
@app.callback(
    Output('history-download-excel', 'data'),
    Input('history-btn-export', 'nClicks'),
    prevent_initial_call=True
)
def export_excel(nClicks):
    if not nClicks:
        return dash.no_update
    
    # 导出时不需要前端的 Tag 组件，直接去数据库拿原始数据
    raw_data = dao_price_history.get_all_price_history()
    df = pd.DataFrame(raw_data)
    
    # 丢弃内部使用的主键，格式化时间并重命名表头
    df = df.drop(columns=['history_id'], errors='ignore')
    if 'change_time' in df.columns:
        df['change_time'] = pd.to_datetime(df['change_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
    df = df.rename(columns={
        'change_time': '变更时间', 
        'goods_id': '商品ID', 
        'goods_name': '商品名称',
        'price': '价格',
        'change_type': '变更类型'
    })
    
    # 调整导出列的顺序
    columns_order = ['变更时间', '商品ID', '商品名称', '价格', '变更类型']
    df = df[columns_order]
    
    return dcc.send_data_frame(df.to_excel, "商品价格变更分析导出.xlsx", index=False)