from server import app
from dash.dependencies import Input, Output
import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.sql_db.dao import dao_price_history

def load_goods_options():
    """供 View 层初始化加载和刷新下拉框选项"""
    try:
        raw_options = dao_price_history.get_goods_options_for_trend()
        return [{'label': str(opt['label']), 'value': int(opt['value'])} for opt in raw_options]
    except Exception as e:
        return []

def get_empty_fig(message):
    fig = go.Figure()
    fig.update_layout(
        title=message,
        xaxis={'visible': False}, 
        yaxis={'visible': False}, 
        template='simple_white',
        annotations=[{
            "text": message,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 16, "color": "gray"}
        }]
    )
    return fig

# --- 【拆分后的独立回调 1】：专属负责“下拉框的刷新” ---
# 只有在明确点击刷新按钮时才去更新下拉框（页面初始化由 View 负责，这里跳过）
@app.callback(
    Output('trend-goods-select', 'options'),
    Input('trend-btn-refresh', 'nClicks'),
    prevent_initial_call=True
)
def update_options_on_refresh(nClicks):
    if nClicks:
        return load_goods_options()
    return dash.no_update

# --- 【拆分后的独立回调 2】：专属负责“折线图的渲染” ---
# 只要下拉框的值变化，或者点击了刷新，图表就会自动重新计算
@app.callback(
    Output('trend-chart', 'figure'),
    [
        Input('trend-goods-select', 'value'),
        Input('trend-btn-refresh', 'nClicks')
    ]
)
def update_trend_chart(selected_goods_ids, nClicks):
    if not selected_goods_ids:
        return get_empty_fig("请在上方的下拉框中选择至少一个商品查看价格趋势。")

    records = dao_price_history.get_price_history_by_goods_ids(selected_goods_ids)
    if not records:
        return get_empty_fig("选中的商品暂无价格变更历史记录。")

    df = pd.DataFrame(records)
    df = df.dropna(subset=['change_time', 'price'])
    if df.empty:
        return get_empty_fig("选中商品的历史数据不完整（可能缺失时间戳）。")

    df['change_time'] = pd.to_datetime(df['change_time'])
    df['date'] = df['change_time'].dt.normalize() 
    df['price'] = df['price'].astype(float) 

    df = df.sort_values('change_time')
    df_daily = df.drop_duplicates(subset=['goods_id', 'date'], keep='last')

    try:
        max_date = df_daily['date'].max()
        end_date = max(pd.Timestamp.today().normalize(), max_date) if not pd.isna(max_date) else pd.Timestamp.today().normalize()
    except:
        end_date = pd.Timestamp.today().normalize()
        
    start_date = end_date - pd.Timedelta(days=30)
    date_range = pd.date_range(start=start_date, end=end_date)

    plot_data = []
    for gid, group in df_daily.groupby('goods_id'):
        good_name = group['goods_name'].iloc[-1] 
        group = group.set_index('date')
        all_dates = group.index.union(date_range).sort_values().unique()
        group_reindexed = group.reindex(all_dates)
        group_reindexed['price'] = group_reindexed['price'].ffill().bfill()
        group_reindexed['goods_name'] = good_name
        group_reindexed['goods_id'] = gid
        
        group_final = group_reindexed.loc[start_date:end_date].copy()
        group_final = group_final.rename_axis('date').reset_index()
        plot_data.append(group_final)

    if not plot_data:
        return get_empty_fig("所选商品在近一个月内暂无可追溯的价格数据。")
        
    final_df = pd.concat(plot_data, ignore_index=True)
    
    fig = px.line(
        final_df, x='date', y='price', color='goods_name', markers=True, 
        title="商品近一个月价格变化趋势", labels={'date': '日期', 'price': '记录价格', 'goods_name': '商品名称'}
    )
    fig.update_layout(hovermode="x unified", template="plotly_white", legend_title_text='对比商品', yaxis_title="价格 (元)", xaxis_title="日期")
    
    return fig