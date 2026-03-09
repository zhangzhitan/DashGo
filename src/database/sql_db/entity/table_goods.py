import datetime
from peewee import CharField, IntegerField, ForeignKeyField, DecimalField, AutoField, DateTimeField
from ..conn import db
from .table_user import BaseModel

# 1. 维表：IP、角色、类目
class DimIP(BaseModel):
    ip_name = CharField(primary_key=True)
    ip_remark = CharField(max_length=128)
    class Meta: table_name = 'merchandise_dim_ip'

class DimCharacter(BaseModel):
    ip = ForeignKeyField(DimIP, backref='characters')
    character_name = CharField(max_length=32)
    character_remark = CharField(max_length=128)
    class Meta: 
        table_name = 'merchandise_dim_character'
        indexes = (
            (('ip', 'character_name'), True),
        )

class DimSeries(BaseModel):
    ip = ForeignKeyField(DimIP, backref='series')
    series_name = CharField(max_length=32)
    series_batch = CharField(max_length=32)
    series_remark = CharField(max_length=128)
    class Meta: 
        table_name = 'merchandise_dim_series'
        indexes = (
            (('ip', 'series_name'), True),
        )

# 2. 商品主表
class Goods(BaseModel):
    goods_id = AutoField()
    goods_name = CharField(max_length=128)
    
    # === 关联三大维度表 ===
    ip = ForeignKeyField(DimIP, backref='goods')
    # 建议加上 null=True，因为有些商品可能没有特定系列，或者属于“全员/无角色”周边
    series = ForeignKeyField(DimSeries, backref='goods', null=True)
    character = ForeignKeyField(DimCharacter, backref='goods', null=True)
    
    original_price = DecimalField(max_digits=10, decimal_places=2)
    # 动态数据建议在 DAO 层通过计算逻辑得出，或在此预留统计字段
    stock_self = IntegerField(default=0, help_text='自留数量')
    
    class Meta: 
        table_name = 'merchandise_goods_main'

# 3. 商品价格变更历史表 (新增)
class GoodsPriceHistory(BaseModel):
    history_id = AutoField()
    # 注意：这里不使用 ForeignKeyField，防止商品删除时引发级联删除或外键约束报错
    goods_id = IntegerField(help_text='商品ID')
    goods_name = CharField(max_length=128, help_text='商品名称')
    price = DecimalField(max_digits=10, decimal_places=2, help_text='记录时的价格')
    change_type = CharField(max_length=32, help_text='变更类型：新增/修改/删除/导入')
    change_time = DateTimeField(default=datetime.datetime.now, help_text='变更时间')
    
    class Meta: 
        table_name = 'merchandise_goods_price_history'