import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
from dash_components.card import render as create_card

def render_content():
    return html.Div([ 
        dbc.Row([
            dbc.Col(create_card("当前总库存", "0", id="total-stock-card"), width=3),
            dbc.Col(create_card("累计销售额", "¥0", id="total-sales-card"), width=3),
            dbc.Col(create_card("待出货商品", "0", id="pending-items-card"), width=3),
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardHeader("库存明细管理"),
            dbc.CardBody([
                dbc.Button("新增进货", id="btn-add-purchase", color="primary", className="mb-3"),
                dash_table.DataTable(
                    id='inventory-table',
                    columns=[
                        {"name": "商品名称", "id": "goods_name"},
                        {"name": "IP", "id": "ip_id"},
                        {"name": "当前库存", "id": "stock_total"},
                        {"name": "已售", "id": "sold_count"},
                        {"name": "待售数量", "id": "stock_for_sale"}
                    ],
                    data=[],
                    page_size=10
                )
            ])
        ]),
        
        # 隐藏的弹窗：用于输入进货信息
        dbc.Modal([
            dbc.ModalHeader("录入进货信息"),
            dbc.ModalBody([
                dbc.Input(id="in-goods-id", placeholder="商品ID"),
                dbc.Input(id="in-buy-price", placeholder="购入单价", type="number", className="mt-2"),
                dbc.Input(id="in-buy-count", placeholder="购入数量", type="number", className="mt-2"),
            ]),
            dbc.ModalFooter(dbc.Button("提交", id="btn-submit-purchase", color="success"))
        ], id="modal-purchase")
    ])