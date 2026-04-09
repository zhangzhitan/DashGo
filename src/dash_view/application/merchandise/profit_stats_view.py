import dash
from dash import html, dcc
import feffery_antd_components as fac
import datetime

title = "每日数据统计"
icon = None
order = 11
access_metas = ['每日数据统计视图']

def render_content(menu_access, **kwargs):
    # Default to recent 30 days
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')

    return html.Div([
        fac.AntdCard([
            fac.AntdSpace([
                fac.AntdDateRangePicker(
                    id='profit-stats-date-range',
                    defaultValue=[start_date, end_date],
                    allowClear=False,
                    style={'width': '260px'}
                ),
            ], wrap=True)
        ], title='筛选条件', style={'marginBottom': '20px'}),
        
        fac.AntdRow([
            fac.AntdCol(
                fac.AntdCard(
                    dcc.Loading(dcc.Graph(id='profit-stats-chart', style={'height': '400px'})),
                    title="收入与利润概览"
                ), span=24
            )
        ], style={'marginBottom': '20px'}),
        
        fac.AntdCard(
            fac.AntdTable(
                id='profit-stats-table',
                columns=[
                    {'title': '统计日期', 'dataIndex': 'stat_date', 'align': 'center'},
                    {'title': '当日进货总数', 'dataIndex': 'total_in_count', 'align': 'center'},
                    {'title': '当日出货总数', 'dataIndex': 'total_out_count', 'align': 'center'},
                    {'title': '当日总花费', 'dataIndex': 'total_cost', 'align': 'center'},
                    {'title': '当日总收入', 'dataIndex': 'total_income', 'align': 'center'},
                    {'title': '利润1(收入-花费)', 'dataIndex': 'profit_1', 'align': 'center'},
                    {'title': '利润2(商品差价)', 'dataIndex': 'profit_2', 'align': 'center'},
                ],
                data=[],
                bordered=True,
                pagination={'pageSize': 10}
            ),
            title="详细数据"
        )
    ], style={'padding': '20px'})
