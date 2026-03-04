from dash import Output, Input, State, callback
from database.sql_db.dao.dao_merchandise import add_purchase_record, get_inventory_summary, Goods

@callback(
    [Output('inventory-table', 'data'),
     Output('total-stock-card', 'children'),
     Output('modal-purchase', 'is_open')],
    [Input('btn-submit-purchase', 'n_clicks')],
    [State('in-goods-id', 'value'),
     State('in-buy-price', 'value'),
     State('in-buy-count', 'value')],
    prevent_initial_call=True
)
def handle_purchase_and_refresh(n_clicks, g_id, price, count):
    if n_clicks:
        # 1. 调用 DAO 更新数据库
        success = add_purchase_record(g_id, price, count, "闲鱼/手动录入", datetime.now())
        
        # 2. 查询最新数据
        new_data = list(Goods.select().dicts())
        summary = get_inventory_summary()
        total_stock = sum(item['total_stock'] for item in summary)
        
        # 3. 返回更新后的界面元素
        return new_data, str(total_stock), False
    return [], "0", False