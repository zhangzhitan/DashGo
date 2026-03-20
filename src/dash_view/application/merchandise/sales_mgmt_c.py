from server import app
from dash.dependencies import Input, Output, State
import dash
import pandas as pd
from database.sql_db.dao import dao_sales
from dash_components import MessageManager
from dash import dcc 

def get_table_data():
    records = dao_sales.get_all_sales_orders()
    for item in records:
        item['key'] = str(item['order_id'])
        item['order_date'] = item['order_date'].strftime('%Y-%m-%d %H:%M') if item['order_date'] else ''
        # 【新增】：为表格渲染编辑按钮
        item['operation'] = [{'content': '查看/编辑', 'type': 'primary', 'custom': f"edit:{item['order_id']}"}]
    return records

# --- 1. 新增/编辑弹窗的打开与回显 ---
@app.callback(
    [
        Output('sale-add-modal', 'visible'),
        Output('sale-add-modal', 'title'),
        Output('sale-form-order-id', 'data'),
        Output('sale-form-ext-no', 'value'),
        Output('sale-form-channel', 'value'),
        Output('sale-form-status', 'value'),
        Output('sale-form-address', 'value'),
        Output('sale-temp-items-store', 'data', allow_duplicate=True)
    ],
    [Input('sale-btn-add', 'nClicks'),
     Input('sale-mgmt-table', 'nClicksButton')],
    [State('sale-mgmt-table', 'clickedCustom')],
    prevent_initial_call=True
)
def open_modal(btn_add, btn_edit, clickedCustom):
    ctx = dash.callback_context
    if not ctx.triggered:
        return [dash.no_update] * 8
        
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'sale-btn-add':
        return True, '新增出货单', None, '', '', '待发货', '', []
        
    elif triggered_id == 'sale-mgmt-table' and clickedCustom:
        action, order_id_str = clickedCustom.split(':', 1)
        if action == 'edit':
            order_id = int(order_id_str)
            order_info, details = dao_sales.get_order_full_info(order_id)
            # 【新增】：编辑回显时，为每行明细添加"删除"按钮
            for item in details:
                item['operation'] = [{'content': '删除', 'type': 'link', 'danger': True, 'custom': f"delete:{item['goods_id']}"}]
            return (True, '编辑出货单', order_id, 
                    order_info['external_order_no'], order_info['channel_id'], 
                    order_info['order_status'], order_info['shipping_address'], details)
                    
    return [dash.no_update] * 8

# --- 2. 级联筛选逻辑 ---
@app.callback(
    [
        Output('sale-filter-series', 'options'),
        Output('sale-filter-char', 'options'),
        Output('sale-item-goods', 'options'),
        Output('sale-filter-series', 'value'),
        Output('sale-filter-char', 'value'),
        Output('sale-item-goods', 'value', allow_duplicate=True)
    ],
    [
        Input('sale-filter-ip', 'value'),
        Input('sale-filter-series', 'value'),
        Input('sale-filter-char', 'value')
    ],
    prevent_initial_call=True
)
def update_filters(ip_v, series_v, char_v):
    ctx = dash.callback_context
    if not ctx.triggered:
        return [dash.no_update] * 6
        
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # 如果改变了 IP，清空系列和角色并重新获取列表
    if triggered_id == 'sale-filter-ip':
        series_opts = dao_sales.get_series_options(ip_v)
        char_opts = dao_sales.get_char_options(ip_v)
        goods_opts = dao_sales.get_goods_options_filtered(ip_v, None, None)
        return series_opts, char_opts, goods_opts, None, None, None
        
    # 如果仅改变了系列或角色，更新商品列表
    goods_opts = dao_sales.get_goods_options_filtered(ip_v, series_v, char_v)
    return dash.no_update, dash.no_update, goods_opts, dash.no_update, dash.no_update, None

# --- 3. 将选中的商品添加到临时明细列表 / 更新明细 / 单行删除 / 清空明细 ---
@app.callback(
    [
        Output('sale-temp-items-store', 'data'),
        Output('sale-item-goods', 'value'), 
        Output('sale-item-price', 'value'),
        Output('sale-item-qty', 'value')
    ],
    [Input('sale-btn-add-item', 'nClicks'),
     Input('sale-btn-clear-item', 'nClicks'),
     Input('sale-temp-items-table', 'nClicksButton')], # 【新增】监听表格内按钮点击
    [
        State('sale-item-goods', 'value'),
        State('sale-item-goods', 'options'),
        State('sale-item-price', 'value'),
        State('sale-item-qty', 'value'),
        State('sale-temp-items-store', 'data'),
        State('sale-temp-items-table', 'clickedCustom') # 【新增】获取表格内被点击的自定义参数
    ],
    prevent_initial_call=True
)
def manage_store(add_clicks, clear_clicks, tbl_clicks, goods_id, goods_options, price, qty, current_items, clickedCustom):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == 'sale-btn-clear-item':
        return [], None, None, None

    # 【新增】处理表格行内的“单行删除”逻辑
    if triggered_id == 'sale-temp-items-table' and clickedCustom:
        action, target_goods_id = clickedCustom.split(':', 1)
        if action == 'delete':
            current_items = [item for item in current_items if str(item['goods_id']) != target_goods_id]
            return current_items, dash.no_update, dash.no_update, dash.no_update

    if triggered_id == 'sale-btn-add-item':
        if not goods_id or price is None or qty is None:
            MessageManager.warning("请填写完整的商品、单价和数量信息")
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
        # 【新增】判断该商品是否已在明细中
        existing_item = next((item for item in current_items if str(item['goods_id']) == str(goods_id)), None)
        
        if existing_item:
            # 如果商品存在，则是“改”操作：更新它的数量和价格
            existing_item['qty'] = int(qty)
            existing_item['price'] = float(price)
            existing_item['subtotal'] = round(float(price) * int(qty), 2)
            MessageManager.success("已更新该商品信息")
        else:
            # 正常“增”操作：添加到列表末尾
            goods_name = next((g['label'] for g in goods_options if g['value'] == goods_id), '未知商品')
            subtotal = float(price) * int(qty)
            
            new_item = {
                'key': str(goods_id),
                'goods_id': goods_id,
                'goods_name': goods_name,
                'price': float(price),
                'qty': int(qty),
                'subtotal': round(subtotal, 2),
                # 为新行也打上操作标识
                'operation': [{'content': '删除', 'type': 'link', 'danger': True, 'custom': f"delete:{goods_id}"}]
            }
            current_items.append(new_item)
        return current_items, None, None, None

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

# --- 4. 监听临时明细列表变化，自动渲染表格并计算总价 ---
@app.callback(
    [
        Output('sale-temp-items-table', 'data'),
        Output('sale-total-display', 'children')
    ],
    Input('sale-temp-items-store', 'data'),
    prevent_initial_call=True
)
def update_temp_table(items):
    total = sum(item['subtotal'] for item in items)
    return items, f"{total:.2f}"

# --- 5. 提交订单入库 ---
@app.callback(
    [
        Output('sale-mgmt-table', 'data', allow_duplicate=True),
        Output('sale-add-modal', 'visible', allow_duplicate=True)
    ],
    Input('sale-add-modal', 'okCounts'),
    [
        State('sale-form-order-id', 'data'),
        State('sale-form-ext-no', 'value'),
        State('sale-form-channel', 'value'),
        State('sale-form-status', 'value'),
        State('sale-form-address', 'value'),
        State('sale-temp-items-store', 'data')
    ],
    prevent_initial_call=True
)
def submit_order(okCounts, order_id, ext_no, channel, status, address, items):
    if not ext_no or not items:
        MessageManager.warning("外部单号和订单明细不能为空")
        return dash.no_update, dash.no_update
        
    success, msg = dao_sales.save_sales_order(
        order_id=order_id,
        external_no=ext_no,
        channel_name=channel or '默认渠道',
        status=status,
        address=address,
        items=items
    )
    
    if success:
        MessageManager.success(f"{'更新' if order_id else '创建'}成功")
        return get_table_data(), False
    else:
        MessageManager.error(f"操作失败: {msg}")
        return dash.no_update, dash.no_update

# --- 6. 导出订单与明细数据至 Excel ---
@app.callback(
    Output('sale-download-excel', 'data'),
    Input('sale-btn-export', 'nClicks'),
    prevent_initial_call=True
)
def export_excel(nClicks):
    if not nClicks:
        return dash.no_update
        
    raw_data = dao_sales.get_export_data()
    if not raw_data:
        MessageManager.warning("暂无数据可导出")
        return dash.no_update
        
    df = pd.DataFrame(raw_data)
    # 格式化时间并重命名列
    if 'order_date' in df.columns:
        df['order_date'] = pd.to_datetime(df['order_date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
    df = df.rename(columns={
        'external_order_no': '外部单号', 'order_status': '发货状态',
        'channel': '渠道', 'order_date': '下单时间',
        'shipping_address': '收货地址', 'goods_name': '商品名称',
        'sale_price': '售出单价', 'sale_count': '售出数量',
        'subtotal': '明细小计', 'total_amount': '订单总价'
    })
    
    # 调整导出列顺序，让订单信息在前，明细在后
    cols = ['外部单号', '渠道', '发货状态', '下单时间', '收货地址', '订单总价', '商品名称', '售出单价', '售出数量', '明细小计']
    df = df[cols]
    
    return dcc.send_data_frame(df.to_excel, "出货订单明细报表.xlsx", index=False)