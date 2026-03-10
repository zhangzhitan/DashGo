import dash
from dash import html, dcc
import feffery_antd_components as fac
from dash_view.application.merchandise.price_trend_c import load_goods_options

# --- 必须定义的元数据 ---
title = "价格趋势分析"
icon = None
order = 6 # 放在价格变更数据分析之后
access_metas = ['价格趋势分析'] 

def render_content(menu_access, **kwargs):
    return html.Div([
        # 工具栏：商品筛选
        fac.AntdSpace([
            html.Span("选择商品对比："),
            fac.AntdSelect(
                id='trend-goods-select',
                mode='multiple',
                placeholder='请选择需要查看趋势的商品（可多选）',
                options=load_goods_options(),
                style={'width': '400px'},
                maxTagCount=3,
                allowClear=True
            ),
            fac.AntdButton('刷新数据', id='trend-btn-refresh', type='primary')
        ], style={'marginBottom': '20px', 'display': 'flex', 'alignItems': 'center'}),
        
        # 图表展示区
        fac.AntdSpin(
            html.Div([
                dcc.Graph(id='trend-chart', style={'height': '600px'})
            ]),
            text='数据加载与计算中...'
        )
    ], style={'padding': '20px', 'backgroundColor': '#fff'})