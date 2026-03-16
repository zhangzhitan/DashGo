import dash
from dash import html, dcc
import feffery_antd_components as fac
from database.sql_db.dao import dao_sales # 复用出货单里的下拉选项查询

title = "实时库存盘点"
icon = None
order = 7 # 放在进货管理后面
access_metas = ['实时库存盘点'] 

def render_content(menu_access, **kwargs):
    return html.Div([
        # 顶部工具栏与筛选器
        fac.AntdSpace([
            fac.AntdSelect(id='inv-status-filter-ip', options=dao_sales.get_ip_options(), placeholder='筛选IP', style={'width': 150}, allowClear=True),
            fac.AntdSelect(id='inv-status-filter-series', placeholder='筛选系列', style={'width': 150}, allowClear=True),
            fac.AntdSelect(id='inv-status-filter-char', placeholder='筛选角色', style={'width': 150}, allowClear=True),
            fac.AntdButton('查询 / 刷新', id='inv-status-btn-search', type='primary'),
            fac.AntdButton('导出 Excel', id='inv-status-btn-export'),
            dcc.Download(id='inv-status-download-excel')
        ], style={'marginBottom': '15px'}),
        
        # 实时库存状态表
        fac.AntdSpin(
            fac.AntdTable(
                id='inv-status-table',
                columns=[
                    {'title': '商品ID', 'dataIndex': 'goods_id', 'width': 80},
                    {'title': '所属IP', 'dataIndex': 'ip_name'},
                    {'title': '所属系列', 'dataIndex': 'series_name'},
                    {'title': '所属角色', 'dataIndex': 'character_name'},
                    {'title': '商品名称', 'dataIndex': 'goods_name'},
                    {'title': '累计进货 (件)', 'dataIndex': 'total_buy'},
                    {'title': '累计出货 (件)', 'dataIndex': 'total_sale'},
                    {'title': '当前库存结余', 'dataIndex': 'current_stock'},
                ],
                data=[], 
                bordered=True,
                pagination=True
            ),
            text='正在实时计算库存...'
        )
    ], style={'padding': '20px'})