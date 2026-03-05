import dash
from dash import html, dcc
import feffery_antd_components as fac
from i18n import t__default

# 【重点1】直接从回调文件中引入获取数据的方法
from dash_view.application.merchandise.ip_mgmt_c import get_table_data

# --- 必须定义的元数据 ---
title = "IP管理"
icon = None
order = 1 
# 注意：这里定义为列表，如果框架要求唯一性检查，AccessFactory 那边会有逻辑处理
access_metas = ['IP管理'] 

def render_content(menu_access, **kwargs):
    return html.Div([
        # 工具栏
        fac.AntdSpace([
            fac.AntdButton('新增 IP', id='ip-btn-add', type='primary'),
            
            dcc.Upload(
                id='ip-upload-excel',
                children=fac.AntdButton('导入 Excel (ip_name, ip_remark)'),
                multiple=False
            ),
            
            fac.AntdButton('导出 Excel', id='ip-btn-export'),
            dcc.Download(id='ip-download-excel')
        ], style={'marginBottom': '15px'}),
        
        fac.AntdTable(
                    id='ip-mgmt-table',
                    columns=[
                        {'title': 'IP名称', 'dataIndex': 'ip_name'},
                        {'title': '备注/描述', 'dataIndex': 'ip_remark'},
                        {'title': '操作', 'dataIndex': 'operation', 'renderOptions': {'renderType': 'button'}}
                    ],
                    # 直接获取最新数据
                    data=get_table_data(), 
                    bordered=True,
                    
                    # 【修复报错】在当前版本中，仅传 True 开启默认分页即可
                    pagination=True
                ),

        # 新增/编辑弹窗
        fac.AntdModal(
            id='ip-edit-modal',
            title='编辑 IP',
            visible=False,
            renderFooter=True,
            okText='保存',
            cancelText='取消',
            children=[
                fac.AntdForm([
                    fac.AntdFormItem(
                        fac.AntdInput(id='ip-form-name'),
                        label='IP名称',
                        required=True
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(id='ip-form-remark', mode='text-area'),
                        label='备注'
                    ),
                    dcc.Store(id='ip-form-old-name')
                ])
            ]
        ),

        # 删除确认弹窗
        fac.AntdModal(
            id='ip-delete-modal',
            title='确认删除',
            visible=False,
            renderFooter=True,
            okText='确认删除',  
            cancelText='取消',
            okButtonProps={'danger': True},
            children=[
                html.Span('确定要删除IP：'),
                html.B(id='ip-delete-name', style={'color': 'red'}),
                html.Span(' 吗？（此操作不可逆转，且可能影响依赖此IP的商品！）')
            ]
        )
    ], style={'padding': '20px'})