from server import app
from dash.dependencies import Input, Output
import dash
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
from database.sql_db.dao import dao_price_history

def load_goods_options():
    """供 View 层初始化加载下拉框选项"""
    return dao_price_history.get_goods_options_for_trend()

def get_empty_fig(message):
    """专门用于生成带有提示信息的空图表"""
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

# --- 1. 监听下拉框选择，渲染折线图 ---
@app.callback(
    Output('trend-chart', 'figure'),
    [
        Input('trend-goods-select', 'value'),
        Input('trend-btn-refresh', 'nClicks') # 刷新按钮
    ]
)
def update_trend_chart(selected_goods_ids, nClicks):
    if not selected_goods_ids:
        return get_empty_fig("请在上方的下拉框中选择至少一个商品查看价格趋势。")

    # 1. 获取选中商品的所有历史记录
    records = dao_price_history.get_price_history_by_goods_ids(selected_goods_ids)
    if not records:
        return get_empty_fig("选中的商品暂无价格变更历史记录。")

    # 2. 转换为 Pandas DataFrame 并清洗数据
    df = pd.DataFrame(records)
    df['change_time'] = pd.to_datetime(df['change_time'])
    df['date'] = df['change_time'].dt.normalize() # 将时间归一化到当天的 00:00:00
    
    # 【核心修复1】：强制将价格转换为浮点数，防止数据库 Decimal 格式导致 Plotly 坐标轴解析失败
    df['price'] = df['price'].astype(float) 

    # 按时间升序排序
    df = df.sort_values('change_time')

    # 如果一天有多条变化，取最后一条 (keep='last')
    df_daily = df.drop_duplicates(subset=['goods_id', 'date'], keep='last')

    # 【核心修复2】：取当前时间与数据最新时间的取最大值作为截止日，防止服务器时区差异切掉当天数据
    end_date = max(pd.Timestamp.today().normalize(), df_daily['date'].max())
    start_date = end_date - pd.Timedelta(days=30)
    date_range = pd.date_range(start=start_date, end=end_date)

    plot_data = []

    # 按商品分组进行处理
    for gid, group in df_daily.groupby('goods_id'):
        good_name = group['goods_name'].iloc[-1] # 取最新名称
        group = group.set_index('date')
        
        # 将该商品现有的日期 和 近30天连续日期 合并
        all_dates = group.index.union(date_range).sort_values().unique()
        
        # 重建索引，使得每一天都有行
        group_reindexed = group.reindex(all_dates)
        
        # 【核心修复3】：双向填充 (ffill + bfill)
        # 以前只用了 ffill(向下填充)，导致第一条记录前的日期全是空值。
        # 加上 bfill(向上兜底) 后，即使数据库里只有 1 条今天的新增记录，也会补齐过去30天的价格，从而画出一条漂亮的水平直线！
        group_reindexed['price'] = group_reindexed['price'].ffill().bfill()
        
        # 补充其他静态字段
        group_reindexed['goods_name'] = good_name
        group_reindexed['goods_id'] = gid
        
        # 过滤出仅在近 30 天区间的数据
        group_final = group_reindexed.loc[start_date:end_date].copy()
        
        # 将日期索引转回普通列
        group_final = group_final.rename_axis('date').reset_index()
        plot_data.append(group_final)

    # 3. 合并清洗好的数据并绘图
    if not plot_data:
        return get_empty_fig("所选商品在近一个月内暂无可追溯的价格数据。")
        
    final_df = pd.concat(plot_data, ignore_index=True)
    
    # 绘制折线图
    fig = px.line(
        final_df, 
        x='date', 
        y='price', 
        color='goods_name', 
        markers=True, # 显示数据点
        title="商品近一个月价格变化趋势",
        labels={'date': '日期', 'price': '记录价格', 'goods_name': '商品名称'}
    )
    
    # 优化图表样式
    fig.update_layout(
        hovermode="x unified", # 鼠标悬停时显示该日期下所有商品的对比十字准星
        template="plotly_white",
        legend_title_text='对比商品',
        yaxis_title="价格 (元)",
        xaxis_title="日期"
    )
    
    return fig