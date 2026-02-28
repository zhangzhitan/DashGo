import feffery_antd_components as fac
from dash import dcc, html
from common.utilities.util_menu_access import MenuAccess

title = '数据盘点'
order = 10
access_metas = ('数据盘点-查询', '数据盘点-导入')

def render_content(menu_access: MenuAccess, **kwargs):
    # 打印 menu_access 的所有属性和值到终端 (cmd)
    # print("====== MenuAccess 属性大揭秘 ======")
    # print(dir(menu_access)) 
    # print(vars(menu_access))
    # print("==================================")
    can_import = menu_access.has_access('数据盘点-导入')

    return fac.AntdCol(
        [
            # --- 筛选与操作栏 ---
            fac.AntdRow(
                [
                    fac.AntdCol(
                        fac.AntdSpace(
                            [
                                # 筛选组件：项目名称
                                fac.AntdSelect(
                                    id='inventory-filter-project',
                                    placeholder='筛选项目',
                                    style={'width': '200px'},
                                    allowClear=True
                                ),
                                # 筛选组件：功能名称
                                fac.AntdSelect(
                                    id='inventory-filter-function',
                                    placeholder='筛选功能',
                                    style={'width': '200px'},
                                    allowClear=True
                                ),
                                # 搜索按钮
                                fac.AntdButton(
                                    '查询',
                                    id='inventory-btn-search',
                                    type='primary',
                                    icon=fac.AntdIcon(icon='antd-search')
                                ),
                            ]
                        ),
                        flex=1
                    ),
                    fac.AntdCol(
                        # 导入按钮（带权限控制）
                        dcc.Upload(
                            id='inventory-upload',
                            children=fac.AntdButton(
                                '导入 Excel',
                                icon=fac.AntdIcon(icon='antd-upload'),
                                type='default' # 样式区别于查询
                            ),
                            accept='.xlsx, .xls',
                            multiple=False
                        ) if can_import else html.Div()
                    )
                ],
                justify='space-between',
                style={'marginBottom': '15px'}
            ),

            # --- 数据表格 ---
            fac.AntdTable(
                id='inventory-table',
                columns=[
                    {'title': '项目名称', 'dataIndex': 'project_name', 'width': 120},
                    {'title': '功能名称', 'dataIndex': 'function_name', 'width': 120},
                    {'title': '数据集名称', 'dataIndex': 'dataset_name', 'width': 150},
                    {'title': '详细数据项', 'dataIndex': 'detailed_data', 'width': 200, 'renderOptions': {'renderType': 'ellipsis'}},
                    {'title': '特殊类别', 'dataIndex': 'sensitive_category', 'width': 120},
                    {'title': '数据主体', 'dataIndex': 'data_subject', 'width': 100},
                    {'title': '主体数量', 'dataIndex': 'subject_amount', 'width': 100},
                    {'title': '最小化要求', 'dataIndex': 'requirement_type', 'width': 120},
                    {'title': '收集来源', 'dataIndex': 'collection_source', 'width': 120},
                    {'title': '收集时间', 'dataIndex': 'collection_time_desc', 'width': 120},
                ],
                data=[], 
                pagination={
                    'current': 1,
                    'pageSize': 10,
                    'total': 0,
                    'showSizeChanger': True
                },
                # remotePagination=True,
                bordered=True,
                # scroll={'x': 1500} # 横向滚动，防止列过多挤压
            )
        ]
    )