from server import app
from dash.dependencies import Input, Output, State
import dash
import pandas as pd
from database.sql_db.dao import dao_purchase
from dash_components import MessageManager
from dash import dcc 

def get_table_data():
    records = dao_purchase.get_all_purchase_orders()
    for item in records:
        item['key'] = str(item['order_id'])
        item['order_date'] = item['order_date'].strftime('%Y-%m-%d %H:%M') if item['order_date'] else ''
        item['operation'] = [{'content': '查看/编辑', 'type': 'primary', 'custom': f"edit:{item['order_id']}"}]
    return records

# --- 1. 新增/编辑弹窗的打开与回显 ---
@app.callback(
    [
        Output('purchase-add-modal', 'visible'),
        Output('purchase-add-modal', 'title'),
        Output('purchase-form-order-id', 'data'),
        Output('purchase-form-ext-no', 'value'),
        Output('purchase-form-channel', 'value'),
        Output('purchase-form-status', 'value'),
        Output('purchase-form-remark', 'value'),
        Output('purchase-temp-items-store', 'data', allow_duplicate=True)
    ],
    [Input('purchase-btn-add', 'nClicks'),
     Input('purchase-mgmt-table', 'nClicksButton')],
    [State('purchase-mgmt-table', 'clickedCustom')],
    prevent_initial_call=True
)
def open_modal(btn_add, btn_edit, clickedCustom):
    ctx = dash.callback_context
    if not ctx.triggered:
        return [dash.no_update] * 8
        
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'purchase-btn-add':
        return True, '新增进货单', None, '', '', '已下单', '', []
        
    elif triggered_id == 'purchase-mgmt-table' and clickedCustom:
        action, order_id_str = clickedCustom.split(':', 1)
        if action == 'edit':
            order_id = int(order_id_str)
            order_info, details = dao_purchase.get_order_full_info(order_id)
            # 【新增】回显渲染删除按钮
            for item in details:
                item['operation'] = [{'content': '删除', 'type': 'link', 'danger': True, 'custom': f"delete:{item['goods_id']}"}]
            return (True, '编辑进货单', order_id, 
                    order_info['external_order_no'], order_info['channel_id'], 
                    order_info['order_status'], order_info['remark'], details)
                    
    return [dash.no_update] * 8

# --- 2. 级联筛选逻辑 ---
@app.callback(
    [
        Output('purchase-filter-series', 'options'),
        Output('purchase-filter-char', 'options'),
        Output('purchase-item-goods', 'options'),
        Output('purchase-filter-series', 'value'),
        Output('purchase-filter-char', 'value'),
        Output('purchase-item-goods', 'value', allow_duplicate=True)
    ],
    [
        Input('purchase-filter-ip', 'value'),
        Input('purchase-filter-series', 'value'),
        Input('purchase-filter-char', 'value')
    ],
    prevent_initial_call=True
)
def update_filters(ip_v, series_v, char_v):
    ctx = dash.callback_context
    if not ctx.triggered:
        return [dash.no_update] * 6
        
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'purchase-filter-ip':
        series_opts = dao_purchase.get_series_options(ip_v)
        char_opts = dao_purchase.get_char_options(ip_v)
        goods_opts = dao_purchase.get_goods_options_filtered(ip_v, None, None)
        return series_opts, char_opts, goods_opts, None, None, None
        
    goods_opts = dao_purchase.get_goods_options_filtered(ip_v, series_v, char_v)
    return dash.no_update, dash.no_update, goods_opts, dash.no_update, dash.no_update, None

# --- 3. 将选中的商品添加到临时明细列表 / 单行删除 / 清空明细 ---
@app.callback(
    [
        Output('purchase-temp-items-store', 'data'),
        Output('purchase-item-goods', 'value'), 
        Output('purchase-item-price', 'value'),
        Output('purchase-item-qty', 'value')
    ],
    [Input('purchase-btn-add-item', 'nClicks'),
     Input('purchase-btn-clear-item', 'nClicks'),
     Input('purchase-temp-items-table', 'nClicksButton')], # 【新增】监听表格操作
    [
        State('purchase-item-goods', 'value'),
        State('purchase-item-goods', 'options'),
        State('purchase-item-price', 'value'),
        State('purchase-item-qty', 'value'),
        State('purchase-temp-items-store', 'data'),
        State('purchase-temp-items-table', 'clickedCustom') # 【新增】参数
    ],
    prevent_initial_call=True
)
def manage_store(add_clicks, clear_clicks, tbl_clicks, goods_id, goods_options, price, qty, current_items, clickedCustom):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == 'purchase-btn-clear-item':
        return [], None, None, None

    # 【新增】处理删除特定商品逻辑
    if triggered_id == 'purchase-temp-items-table' and clickedCustom:
        action, target_goods_id = clickedCustom.split(':', 1)
        if action == 'delete':
            current_items = [item for item in current_items if str(item['goods_id']) != target_goods_id]
            return current_items, dash.no_update, dash.no_update, dash.no_update

    if triggered_id == 'purchase-btn-add-item':
        if not goods_id or price is None or qty is None:
            MessageManager.warning("请填写完整的商品、进价和数量信息")
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
        # 【新增】判重并更新逻辑
        existing_item = next((item for item in current_items if str(item['goods_id']) == str(goods_id)), None)
        
        if existing_item:
            existing_item['qty'] = int(qty)
            existing_item['price'] = float(price)
            existing_item['subtotal'] = round(float(price) * int(qty), 2)
            MessageManager.success("已更新该商品信息")
        else:
            goods_name = next((g['label'] for g in goods_options if g['value'] == goods_id), '未知商品')
            subtotal = float(price) * int(qty)
            
            new_item = {
                'key': str(goods_id), 
                'goods_id': goods_id,
                'goods_name': goods_name,
                'price': float(price),
                'qty': int(qty),
                'subtotal': round(subtotal, 2),
                'operation': [{'content': '删除', 'type': 'link', 'danger': True, 'custom': f"delete:{goods_id}"}]
            }
            current_items.append(new_item)
        return current_items, None, None, None

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

# --- 4. 监听临时明细列表变化，自动计算总价 ---
@app.callback(
    [
        Output('purchase-temp-items-table', 'data'),
        Output('purchase-total-display', 'children')
    ],
    Input('purchase-temp-items-store', 'data'),
    prevent_initial_call=True
)
def update_temp_table(items):
    total = sum(item['subtotal'] for item in items)
    return items, f"{total:.2f}"

# --- 5. 提交订单入库 ---
@app.callback(
    [
        Output('purchase-mgmt-table', 'data', allow_duplicate=True),
        Output('purchase-add-modal', 'visible', allow_duplicate=True)
    ],
    Input('purchase-add-modal', 'okCounts'),
    [
        State('purchase-form-order-id', 'data'),
        State('purchase-form-ext-no', 'value'),
        State('purchase-form-channel', 'value'),
        State('purchase-form-status', 'value'),
        State('purchase-form-remark', 'value'),
        State('purchase-temp-items-store', 'data')
    ],
    prevent_initial_call=True
)
def submit_order(okCounts, order_id, ext_no, channel, status, remark, items):
    if not ext_no or not items:
        MessageManager.warning("外部单号和进货明细不能为空")
        return dash.no_update, dash.no_update
        
    success, msg = dao_purchase.save_purchase_order(
        order_id=order_id,
        external_no=ext_no,
        channel_name=channel or '默认渠道',
        status=status,
        remark=remark,
        items=items
    )
    
    if success:
        MessageManager.success(f"{'更新' if order_id else '创建'}成功")
        return get_table_data(), False
    else:
        MessageManager.error(f"操作失败: {msg}")
        return dash.no_update, dash.no_update

# --- 6. 导出进货明细 ---
@app.callback(
    Output('purchase-download-excel', 'data'),
    Input('purchase-btn-export', 'nClicks'),
    prevent_initial_call=True
)
def export_excel(nClicks):
    if not nClicks:
        return dash.no_update
        
    raw_data = dao_purchase.get_export_data()
    if not raw_data:
        MessageManager.warning("暂无数据可导出")
        return dash.no_update
        
    df = pd.DataFrame(raw_data)
    if 'order_date' in df.columns:
        df['order_date'] = pd.to_datetime(df['order_date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
    df = df.rename(columns={
        'external_order_no': '外部单号', 'order_status': '进货状态',
        'channel': '渠道', 'order_date': '进货时间',
        'remark': '备注说明', 'goods_name': '商品名称',
        'buy_price': '进货单价', 'buy_count': '进货数量',
        'subtotal': '明细小计', 'total_amount': '进货单总价'
    })
    
    cols = ['外部单号', '渠道', '进货状态', '进货时间', '备注说明', '进货单总价', '商品名称', '进货单价', '进货数量', '明细小计']
    df = df[cols]
    
    return dcc.send_data_frame(df.to_excel, "进货单明细报表.xlsx", index=False)