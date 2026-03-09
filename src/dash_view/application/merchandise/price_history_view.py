import dash
from dash import html, dcc
import feffery_antd_components as fac
from dash_view.application.merchandise.price_history_c import get_table_data

# --- 必须定义的元数据 ---
title = "价格变更数据分析"
icon = None
order = 5 # 放在商品主表管理之后
access_metas = ['价格变更数据分析'] 

def render_content(menu_access, **kwargs):
    return html.Div([
        # 工具栏：只有导出，没有增删改和导入
        fac.AntdSpace([
            fac.AntdButton('导出 Excel', id='history-btn-export', type='primary'),
            dcc.Download(id='history-download-excel')
        ], style={'marginBottom': '15px'}),
        
        fac.AntdTable(
            id='history-mgmt-table',
            columns=[
                {'title': '变更时间', 'dataIndex': 'change_time', 'width': 200},
                {'title': '商品ID', 'dataIndex': 'goods_id', 'width': 100},
                {'title': '商品名称', 'dataIndex': 'goods_name'},
                {'title': '当时记录价格', 'dataIndex': 'price'},
                {'title': '变更类型', 'dataIndex': 'change_type'}
                # 注意：没有操作列
            ],
            data=get_table_data(), 
            bordered=True,
            pagination=True
        )
    ], style={'padding': '20px'})