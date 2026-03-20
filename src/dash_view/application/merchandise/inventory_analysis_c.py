# src/dash_view/application/dashboard/inventory_analysis_c.py
from server import app
from dash.dependencies import Input, Output, State
import dash
import plotly.graph_objects as go
from database.sql_db.dao import dao_sales
from database.sql_db.dao import dao_inventory_analysis

# --- 1. 级联选项回调 (复用出货单逻辑) ---
@app.callback(
    [Output('analysis-filter-series', 'options'), Output('analysis-filter-char', 'options')],
    [Input('analysis-filter-ip', 'value')],
    prevent_initial_call=True
)
def update_filters(ip_v):
    if not ip_v:
        return [], []
    return dao_sales.get_series_options(ip_v), dao_sales.get_char_options(ip_v)

# --- 2. 核心图表渲染 ---
@app.callback(
    Output('analysis-trend-chart', 'figure'),
    [
        Input('analysis-date-range', 'value'),
        Input('analysis-filter-ip', 'value'),
        Input('analysis-filter-series', 'value'),
        Input('analysis-filter-char', 'value')
    ]
)
def update_chart(date_range, ip_v, series_v, char_v):
    if not date_range:
        return dash.no_update
        
    start_date, end_date = date_range[0], date_range[1]
    
    # 调取分析数据
    data = dao_inventory_analysis.get_analysis_chart_data(start_date, end_date, ip_v, series_v, char_v)
    
    dates = [d['snapshot_date'] for d in data]
    in_qtys = [d['sum_in'] for d in data]
    # 出库用负数表示，柱状图会画在X轴下方，非常直观！
    out_qtys = [-d['sum_out'] for d in data] 
    stock_qtys = [d['sum_stock'] for d in data]
    
    fig = go.Figure()
    
    # 增加入库柱状图
    fig.add_trace(go.Bar(
        x=dates, y=in_qtys, name="入库量", marker_color='#52c41a', opacity=0.7
    ))
    
    # 增加出库柱状图 (负数向下)
    fig.add_trace(go.Bar(
        x=dates, y=out_qtys, name="出库量", marker_color='#f5222d', opacity=0.7
    ))
    
    # 增加库存结余折线图
    fig.add_trace(go.Scatter(
        x=dates, y=stock_qtys, name="库存结余", 
        mode='lines+markers', line=dict(color='#1890ff', width=3),
        marker=dict(size=6)
    ))

    # 图表布局美化
    fig.update_layout(
        barmode='relative', # 允许正负柱子堆叠在同一天
        hovermode="x unified",
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis=dict(title="日期"),
        yaxis=dict(title="数量 (件)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig