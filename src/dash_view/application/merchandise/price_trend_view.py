import dash
from dash import html, dcc
import feffery_antd_components as fac

# 1. 显式导入 controller，确保回调能在应用中被注册
import dash_view.application.merchandise.price_trend_c as controller

title = "价格趋势分析"
icon = None
order = 6 
access_metas = ['价格趋势分析'] 

def render_content(menu_access, **kwargs):
    # 2. 【核心修复】：利用框架的动态路由特性，每次进入此页面或 F5 刷新时，
    # 都在后端先查好最新数据，直接塞给前端！彻底干掉初始化 Callback 的不稳定性。
    initial_options = controller.load_goods_options()
    
    return html.Div([
        fac.AntdSpace([
            html.Span("选择商品对比："),
            fac.AntdSelect(
                id='trend-goods-select',
                mode='multiple',
                placeholder='请选择需要查看趋势的商品（可多选）',
                options=initial_options,  # 初始加载即带上最新数据
                style={'width': '400px'},
                maxTagCount=3,
                allowClear=True
            ),
            fac.AntdButton('刷新数据', id='trend-btn-refresh', type='primary')
        ], style={'marginBottom': '20px', 'display': 'flex', 'alignItems': 'center'}),
        
        fac.AntdSpin(
            html.Div([
                dcc.Graph(id='trend-chart', style={'height': '600px'})
            ]),
            text='数据加载与计算中...'
        )
    ], style={'padding': '20px', 'backgroundColor': '#fff'})