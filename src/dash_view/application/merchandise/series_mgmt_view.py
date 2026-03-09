import dash
from dash import html, dcc
import feffery_antd_components as fac
from i18n import t__default

from dash_view.application.merchandise.series_mgmt_c import get_table_data

# --- 必须定义的元数据 ---
title = "系列管理"
icon = None
order = 3 
access_metas = ['系列管理'] 

def render_content(menu_access, **kwargs):
    return html.Div([
        # 工具栏
        fac.AntdSpace([
            fac.AntdButton('新增系列', id='series-btn-add', type='primary'),
            
            dcc.Upload(
                id='series-upload-excel',
                children=fac.AntdButton('导入 Excel (ip_name, series_name, series_batch, series_remark)'),
                multiple=False
            ),
            
            fac.AntdButton('导出 Excel', id='series-btn-export'),
            dcc.Download(id='series-download-excel')
        ], style={'marginBottom': '15px'}),
        
        fac.AntdTable(
            id='series-mgmt-table',
            columns=[
                {'title': '所属IP', 'dataIndex': 'ip_name'},
                {'title': '系列名称', 'dataIndex': 'series_name'},
                {'title': '系列批次', 'dataIndex': 'series_batch'},
                {'title': '备注', 'dataIndex': 'series_remark'},
                {'title': '操作', 'dataIndex': 'operation', 'renderOptions': {'renderType': 'button'}}
            ],
            data=get_table_data(), 
            bordered=True,
            pagination=True
        ),

        # 新增/编辑弹窗
        fac.AntdModal(
            id='series-edit-modal',
            title='编辑系列',
            visible=False,
            renderFooter=True,
            okText='保存',
            cancelText='取消',
            children=[
                fac.AntdForm([
                    fac.AntdFormItem(
                        fac.AntdInput(id='series-form-ip', placeholder='输入IP名称，若不存在将自动创建'),
                        label='所属IP',
                        required=True
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(id='series-form-name'),
                        label='系列名称',
                        required=True
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(id='series-form-batch'),
                        label='系列批次'
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(id='series-form-remark', mode='text-area'),
                        label='备注'
                    ),
                    dcc.Store(id='series-form-old-ip'),
                    dcc.Store(id='series-form-old-name')
                ])
            ]
        ),

        # 删除确认弹窗
        fac.AntdModal(
            id='series-delete-modal',
            title='确认删除',
            visible=False,
            renderFooter=True,
            okText='确认删除',  
            cancelText='取消',
            okButtonProps={'danger': True},
            children=[
                html.Span('确定要删除系列：'),
                html.B(id='series-delete-name', style={'color': 'red'}),
                html.Span(' 吗？（此操作不可逆转！）'),
                dcc.Store(id='series-delete-ip-store')
            ]
        )
    ], style={'padding': '20px'})