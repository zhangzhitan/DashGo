# src/dash_view/application/dashboard/inventory_analysis_view.py
import dash
from dash import html, dcc
import feffery_antd_components as fac
from database.sql_db.dao import dao_sales # 复用它的维度查询
import datetime

title = "库存分析趋势"
icon = None
order = 9
access_metas = ['库存分析视图']

def render_content(menu_access, **kwargs):
    # 默认近30天
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')

    return html.Div([
        fac.AntdCard([
            fac.AntdSpace([
                fac.AntdDateRangePicker(
                    id='analysis-date-range',
                    defaultValue=[start_date, end_date],
                    allowClear=False,
                    style={'width': '260px'}
                ),
                fac.AntdSelect(id='analysis-filter-ip', options=dao_sales.get_ip_options(), placeholder='所有IP', style={'width': 120}, allowClear=True),
                fac.AntdSelect(id='analysis-filter-series', placeholder='所有系列', style={'width': 120}, allowClear=True),
                fac.AntdSelect(id='analysis-filter-char', placeholder='所有角色', style={'width': 120}, allowClear=True),
            ], wrap=True)
        ], title='筛选条件', style={'marginBottom': '20px'}),
        
        fac.AntdCard(
            dcc.Loading(dcc.Graph(id='analysis-trend-chart', style={'height': '500px'})),
            title="库存进销趋势概览 (柱线组合)"
        )
    ], style={'padding': '20px'})