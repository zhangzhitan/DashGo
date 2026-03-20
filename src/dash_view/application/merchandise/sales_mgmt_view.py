import dash
from dash import html, dcc
import feffery_antd_components as fac
from dash_view.application.merchandise.sales_mgmt_c import get_table_data
from database.sql_db.dao import dao_sales

title = "出货/订单管理"
icon = None
order = 6
access_metas = ['出货订单管理'] 

def render_content(menu_access, **kwargs):
    return html.Div([
        fac.AntdSpace([
            fac.AntdButton('新增出货单', id='sale-btn-add', type='primary'),
            fac.AntdButton('导出明细 (Excel)', id='sale-btn-export'),
            dcc.Download(id='sale-download-excel')
        ], style={'marginBottom': '15px'}),
        
        fac.AntdTable(
            id='sale-mgmt-table',
            columns=[
                {'title': '外部单号', 'dataIndex': 'external_order_no'},
                {'title': '发货状态', 'dataIndex': 'order_status'},
                {'title': '渠道', 'dataIndex': 'channel'},
                {'title': '总金额', 'dataIndex': 'total_amount'},
                {'title': '下单时间', 'dataIndex': 'order_date'},
                {'title': '操作', 'dataIndex': 'operation', 'renderOptions': {'renderType': 'button'}}
            ],
            data=get_table_data(), 
            bordered=True,
            pagination=True
        ),

        fac.AntdModal(
            id='sale-add-modal',
            title='出货单',
            visible=False,
            width=900,
            renderFooter=True,
            okText='保存订单',
            children=[
                dcc.Store(id='sale-form-order-id'),
                
                fac.AntdDivider("订单基础信息", innerTextOrientation="left"),
                fac.AntdForm([
                    fac.AntdFormItem(fac.AntdInput(id='sale-form-ext-no'), label='外部单号', required=True),
                    fac.AntdFormItem(fac.AntdInput(id='sale-form-channel'), label='出货渠道'),
                    fac.AntdFormItem(
                        fac.AntdSelect(
                            id='sale-form-status',
                            options=[
                                {'label': '预售', 'value': '预售'},
                                {'label': '待发货', 'value': '待发货'},
                                {'label': '待收货', 'value': '待收货'},
                                {'label': '已完成', 'value': '已完成'},
                                {'label': '退货', 'value': '退货'},
                            ],
                            defaultValue='待发货'
                        ), 
                        label='发货状态'
                    ),
                    fac.AntdFormItem(fac.AntdInput(id='sale-form-address'), label='收货地址', style={'width': '300px'}),
                ], layout='inline'),
                
                fac.AntdDivider("添加出货商品", innerTextOrientation="left"),
                fac.AntdSpace([
                    fac.AntdSelect(id='sale-filter-ip', options=dao_sales.get_ip_options(), placeholder='筛选IP', style={'width': 120}, allowClear=True),
                    fac.AntdSelect(id='sale-filter-series', placeholder='筛选系列', style={'width': 120}, allowClear=True),
                    fac.AntdSelect(id='sale-filter-char', placeholder='筛选角色', style={'width': 120}, allowClear=True),
                    fac.AntdSelect(id='sale-item-goods', options=dao_sales.get_goods_options_filtered(), placeholder='选择商品 (必填)', style={'width': 220}),
                    fac.AntdInputNumber(id='sale-item-price', placeholder='单价', min=0, precision=2),
                    fac.AntdInputNumber(id='sale-item-qty', placeholder='数量', min=1, precision=0),
                    fac.AntdButton('添加/修改商品', id='sale-btn-add-item'),
                    fac.AntdButton('清空明细', id='sale-btn-clear-item', danger=True, type='text')
                ], wrap=True),
                
                dcc.Store(id='sale-temp-items-store', data=[]),
                
                html.Div(style={'marginTop': '20px'}),
                fac.AntdTable(
                    id='sale-temp-items-table',
                    columns=[
                        {'title': '商品名称', 'dataIndex': 'goods_name'},
                        {'title': '单价', 'dataIndex': 'price'},
                        {'title': '数量', 'dataIndex': 'qty'},
                        {'title': '小计', 'dataIndex': 'subtotal'},
                        # 【新增】操作列：用于单行删除商品明细
                        {'title': '操作', 'dataIndex': 'operation', 'renderOptions': {'renderType': 'button'}}
                    ],
                    data=[],
                    emptyContent='暂无添加的商品明细'
                ),
                html.Div([
                    html.Strong('订单自动计算总价: ¥ '),
                    html.Span(id='sale-total-display', children='0.00', style={'color': 'red', 'fontSize': '18px'})
                ], style={'textAlign': 'right', 'marginTop': '10px'})
            ]
        )
    ], style={'padding': '20px'})