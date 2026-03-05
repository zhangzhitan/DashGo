import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
# 之前的错误：card.py 里没有 render，只有 Card 类
from dash_components.card import Card as create_card

# --- 必须定义的元数据 ---
title = "商品库存"
icon = None
order = 1 
# 注意：这里定义为列表，如果框架要求唯一性检查，AccessFactory 那边会有逻辑处理
access_metas = ['商品库存'] 

def render_content(menu_access, **kwargs):
    # 保持你原有的逻辑，但注意 create_card 的调用方式需匹配 Card 类的 __init__
    return html.Div([ 
        dbc.Row([
            # 修正调用方式：Card 类接收 title 等关键字参数
            dbc.Col(create_card(title="当前总库存", id="total-stock-card"), width=3),
            dbc.Col(create_card(title="累计销售额", id="total-sales-card"), width=3),
            dbc.Col(create_card(title="待出货商品", id="pending-items-card"), width=3),
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