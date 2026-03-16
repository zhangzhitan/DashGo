import dash
from dash import html, dcc
import feffery_antd_components as fac
from dash_view.application.merchandise.purchase_mgmt_c import get_table_data
from database.sql_db.dao import dao_purchase 

title = "进货/入库管理"
icon = None
order = 6 # 顺序排在出货后面
access_metas = ['进货入库管理'] 

def render_content(menu_access, **kwargs):
    return html.Div([
        fac.AntdSpace([
            fac.AntdButton('新增进货单', id='purchase-btn-add', type='primary'),
            fac.AntdButton('导出明细 (Excel)', id='purchase-btn-export'),
            dcc.Download(id='purchase-download-excel')
        ], style={'marginBottom': '15px'}),
        
        fac.AntdTable(
            id='purchase-mgmt-table',
            columns=[
                {'title': '外部单号', 'dataIndex': 'external_order_no'},
                {'title': '进货状态', 'dataIndex': 'order_status'},
                {'title': '渠道', 'dataIndex': 'channel'},
                {'title': '总金额', 'dataIndex': 'total_amount'},
                {'title': '进货时间', 'dataIndex': 'order_date'},
                {'title': '操作', 'dataIndex': 'operation', 'renderOptions': {'renderType': 'button'}}
            ],
            data=get_table_data(), 
            bordered=True,
            pagination=True
        ),

        fac.AntdModal(
            id='purchase-add-modal',
            title='进货单',
            visible=False,
            width=900, 
            renderFooter=True,
            okText='保存进货单',
            children=[
                dcc.Store(id='purchase-form-order-id'), 
                
                fac.AntdDivider("进货单基础信息", innerTextOrientation="left"),
                fac.AntdForm([
                    fac.AntdFormItem(fac.AntdInput(id='purchase-form-ext-no'), label='进货单号', required=True),
                    fac.AntdFormItem(fac.AntdInput(id='purchase-form-channel'), label='进货渠道(如淘宝)'),
                    fac.AntdFormItem(
                        fac.AntdSelect(
                            id='purchase-form-status',
                            options=[
                                {'label': '已下单', 'value': '已下单'},
                                {'label': '待收货', 'value': '待收货'},
                                {'label': '部分入库', 'value': '部分入库'},
                                {'label': '已入库', 'value': '已入库'},
                                {'label': '退货/异常', 'value': '退货/异常'},
                            ],
                            defaultValue='已下单'
                        ), 
                        label='进货状态'
                    ),
                    fac.AntdFormItem(fac.AntdInput(id='purchase-form-remark'), label='备注说明', style={'width': '300px'}),
                ], layout='inline'),
                
                fac.AntdDivider("添加进货商品", innerTextOrientation="left"),
                fac.AntdSpace([
                    fac.AntdSelect(id='purchase-filter-ip', options=dao_purchase.get_ip_options(), placeholder='筛选IP', style={'width': 120}, allowClear=True),
                    fac.AntdSelect(id='purchase-filter-series', placeholder='筛选系列', style={'width': 120}, allowClear=True),
                    fac.AntdSelect(id='purchase-filter-char', placeholder='筛选角色', style={'width': 120}, allowClear=True),
                    fac.AntdSelect(id='purchase-item-goods', options=dao_purchase.get_goods_options_filtered(), placeholder='选择商品 (必填)', style={'width': 220}),
                    fac.AntdInputNumber(id='purchase-item-price', placeholder='进价', min=0, precision=2),
                    fac.AntdInputNumber(id='purchase-item-qty', placeholder='数量', min=1, precision=0),
                    fac.AntdButton('添加商品', id='purchase-btn-add-item'),
                    fac.AntdButton('清空明细', id='purchase-btn-clear-item', danger=True, type='text')
                ], wrap=True),
                
                dcc.Store(id='purchase-temp-items-store', data=[]),
                
                html.Div(style={'marginTop': '20px'}),
                fac.AntdTable(
                    id='purchase-temp-items-table',
                    columns=[
                        {'title': '商品名称', 'dataIndex': 'goods_name'},
                        {'title': '进货单价', 'dataIndex': 'price'},
                        {'title': '进货数量', 'dataIndex': 'qty'},
                        {'title': '小计', 'dataIndex': 'subtotal'}
                    ],
                    data=[],
                    emptyContent='暂无添加的进货明细'
                ),
                html.Div([
                    html.Strong('进货单自动计算总价: ¥ '),
                    html.Span(id='purchase-total-display', children='0.00', style={'color': 'red', 'fontSize': '18px'})
                ], style={'textAlign': 'right', 'marginTop': '10px'})
            ]
        )
    ], style={'padding': '20px'})