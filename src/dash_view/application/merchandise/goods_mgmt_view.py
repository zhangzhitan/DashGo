import dash
from dash import html, dcc
import feffery_antd_components as fac
from i18n import t__default

from dash_view.application.merchandise.goods_mgmt_c import get_table_data

# --- 必须定义的元数据 ---
title = "商品主表管理"
icon = None
order = 4 
access_metas = ['商品主表管理'] 

def render_content(menu_access, **kwargs):
    return html.Div([
        # 工具栏 (包含筛选条件和操作按钮)
        fac.AntdSpace([
            # 筛选部分
            fac.AntdInput(id='goods-search-ip', placeholder='按IP筛选', allowClear=True, style={'width': '130px'}),
            fac.AntdInput(id='goods-search-series', placeholder='按系列筛选', allowClear=True, style={'width': '130px'}),
            fac.AntdInput(id='goods-search-char', placeholder='按角色筛选', allowClear=True, style={'width': '130px'}),
            fac.AntdButton('查询', id='goods-btn-search', type='primary'),
            
            # 分隔间距
            html.Div(style={'width': '20px'}),
            
            # 操作部分
            fac.AntdButton('新增商品', id='goods-btn-add', type='primary'),
            dcc.Upload(
                id='goods-upload-excel',
                children=fac.AntdButton('导入 Excel (goods_name, ip_name, series_name, character_name, original_price, stock_self, sales_status)'),
                multiple=False
            ),
            fac.AntdButton('导出 Excel', id='goods-btn-export'),
            dcc.Download(id='goods-download-excel')
        ], style={'marginBottom': '15px'}),
        
        fac.AntdTable(
            id='goods-mgmt-table',
            columns=[
                {'title': '商品ID', 'dataIndex': 'goods_id', 'width': 80},
                {'title': '商品名称', 'dataIndex': 'goods_name'},
                {'title': '所属IP', 'dataIndex': 'ip_name'},
                {'title': '所属系列', 'dataIndex': 'series_name'},
                {'title': '所属角色', 'dataIndex': 'character_name'},
                {'title': '原价', 'dataIndex': 'original_price'},
                {'title': '自留库存', 'dataIndex': 'stock_self'},
                {'title': '销售状态', 'dataIndex': 'sales_status'}, # 【新增】销售状态展示
                {'title': '操作', 'dataIndex': 'operation', 'renderOptions': {'renderType': 'button'}}
            ],
            data=get_table_data(), # 初始加载展示所有数据
            bordered=True,
            pagination=True
        ),

        # 新增/编辑弹窗
        fac.AntdModal(
            id='goods-edit-modal',
            title='编辑商品',
            visible=False,
            renderFooter=True,
            okText='保存',
            cancelText='取消',
            width=600,
            children=[
                fac.AntdForm([
                    fac.AntdFormItem(fac.AntdInput(id='goods-form-name'), label='商品名称', required=True),
                    fac.AntdFormItem(fac.AntdInput(id='goods-form-ip', placeholder='输入IP，若不存在将自动创建'), label='所属IP', required=True),
                    fac.AntdFormItem(fac.AntdInput(id='goods-form-series', placeholder='可选，若不存在将自动创建'), label='所属系列'),
                    fac.AntdFormItem(fac.AntdInput(id='goods-form-char', placeholder='可选，若不存在将自动创建'), label='所属角色'),
                    fac.AntdFormItem(fac.AntdInputNumber(id='goods-form-price', min=0, precision=2), label='原价'),
                    fac.AntdFormItem(fac.AntdInputNumber(id='goods-form-stock', min=0, precision=0), label='自留库存'),
                    # 【新增】销售状态字段
                    fac.AntdFormItem(fac.AntdSelect(
                        id='goods-form-status', 
                        options=[
                            {'label': '销售中', 'value': '销售中'},
                            {'label': '临时下架', 'value': '临时下架'},
                            {'label': '下架', 'value': '下架'}
                        ],
                        defaultValue='销售中'
                    ), label='销售状态', required=True),
                    dcc.Store(id='goods-form-id') # 隐藏存储商品ID
                ], labelCol={'span': 5}, wrapperCol={'span': 18})
            ]
        ),

        # 删除确认弹窗
        fac.AntdModal(
            id='goods-delete-modal',
            title='确认删除',
            visible=False,
            renderFooter=True,
            okText='确认删除',  
            cancelText='取消',
            okButtonProps={'danger': True},
            children=[
                html.Span('确定要下架并删除商品：'),
                html.B(id='goods-delete-name', style={'color': 'red'}),
                html.Span(' 吗？（数据将被软删除变为下架状态）'),
                dcc.Store(id='goods-delete-id-store')
            ]
        )
    ], style={'padding': '20px'})