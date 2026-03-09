import dash
from dash import html, dcc
import feffery_antd_components as fac
from i18n import t__default

from dash_view.application.merchandise.character_mgmt_c import get_table_data

# --- 必须定义的元数据 ---
title = "角色管理"
icon = None
order = 2 
access_metas = ['角色管理'] 

def render_content(menu_access, **kwargs):
    return html.Div([
        # 工具栏
        fac.AntdSpace([
            fac.AntdButton('新增角色', id='char-btn-add', type='primary'),
            
            dcc.Upload(
                id='char-upload-excel',
                children=fac.AntdButton('导入 Excel (ip_name, character_name, character_remark)'),
                multiple=False
            ),
            
            fac.AntdButton('导出 Excel', id='char-btn-export'),
            dcc.Download(id='char-download-excel')
        ], style={'marginBottom': '15px'}),
        
        fac.AntdTable(
            id='char-mgmt-table',
            columns=[
                {'title': '所属IP', 'dataIndex': 'ip_name'},
                {'title': '角色名称', 'dataIndex': 'character_name'},
                {'title': '角色备注', 'dataIndex': 'character_remark'},
                {'title': '操作', 'dataIndex': 'operation', 'renderOptions': {'renderType': 'button'}}
            ],
            data=get_table_data(), 
            bordered=True,
            pagination=True
        ),

        # 新增/编辑弹窗
        fac.AntdModal(
            id='char-edit-modal',
            title='编辑角色',
            visible=False,
            renderFooter=True,
            okText='保存',
            cancelText='取消',
            children=[
                fac.AntdForm([
                    fac.AntdFormItem(
                        fac.AntdInput(id='char-form-ip', placeholder='输入IP名称，若不存在将自动创建'),
                        label='所属IP',
                        required=True
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(id='char-form-name'),
                        label='角色名称',
                        required=True
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(id='char-form-remark', mode='text-area'),
                        label='角色备注'
                    ),
                    dcc.Store(id='char-form-old-ip'),
                    dcc.Store(id='char-form-old-name')
                ])
            ]
        ),

        # 删除确认弹窗
        fac.AntdModal(
            id='char-delete-modal',
            title='确认删除',
            visible=False,
            renderFooter=True,
            okText='确认删除',  
            cancelText='取消',
            okButtonProps={'danger': True},
            children=[
                html.Span('确定要删除角色：'),
                html.B(id='char-delete-name', style={'color': 'red'}),
                html.Span(' 吗？（此操作不可逆转！）'),
                dcc.Store(id='char-delete-ip-store') # 隐藏存储IP名以便删除
            ]
        )
    ], style={'padding': '20px'})