from peewee import CharField, IntegerField, DateTimeField, TextField
from ..conn import db
from datetime import datetime

class TableDataInventory(db().Model):
    # 1. 核心索引字段（用于筛选）
    project_name = CharField(verbose_name='项目名称', max_length=100, index=True)
    function_name = CharField(verbose_name='功能名称', max_length=100, index=True)
    
    # 2. 数据集描述
    dataset_name = CharField(verbose_name='数据集名称', max_length=100)
    short_description = CharField(verbose_name='简要描述', max_length=255, null=True)
    
    # 3. 详细内容（反范式设计，直接存长文本，如 "VIN, 排放量, 车速"）
    detailed_data = TextField(verbose_name='详细数据项', null=True)
    
    # 4. 合规与敏感性信息
    data_subject = CharField(verbose_name='数据主体', max_length=100, null=True)
    subject_amount = IntegerField(verbose_name='估计主体数量', default=0)
    sensitive_category = CharField(verbose_name='特殊类别个人数据', max_length=100, null=True) # e.g. 行为轨迹, 生物识别
    requirement_type = CharField(verbose_name='业务最小化要求', max_length=100, null=True) # e.g. 必须, 可选
    
    # 5. 来源与时间
    collection_source = CharField(verbose_name='收集来源', max_length=100, null=True)
    collection_time_desc = CharField(verbose_name='收集时间', max_length=100, null=True) # e.g. "2023-Q4" 或 "实时收集"

    # 系统字段
    create_time = DateTimeField(verbose_name='创建时间', default=datetime.now)
    create_by = CharField(verbose_name='创建人', max_length=50, null=True)

    class Meta:
        table_name = 'biz_data_inventory'