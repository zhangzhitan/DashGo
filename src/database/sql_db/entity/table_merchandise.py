from peewee import CharField, IntegerField, DateTimeField, ForeignKeyField, DecimalField, AutoField
from ..conn import db
from .table_user import BaseModel

# 1. 维表：IP、角色、类目
class DimIP(BaseModel):
    name = CharField(primary_key=True)
    class Meta: table_name = 'dim_ip'

class DimCharacter(BaseModel):
    name = CharField(primary_key=True)
    class Meta: table_name = 'dim_character'

# 2. 商品主表
class Goods(BaseModel):
    goods_id = AutoField()
    goods_name = CharField(max_length=128)
    ip = ForeignKeyField(DimIP, backref='items')
    character = ForeignKeyField(DimCharacter, backref='items')
    original_price = DecimalField(max_digits=10, decimal_places=2)
    # 动态数据建议在 DAO 层通过计算逻辑得出，或在此预留统计字段
    stock_self = IntegerField(default=0, help_text='自留数量')
    
    class Meta: table_name = 'goods_main'

# 3. 进货明细
class PurchaseRecord(BaseModel):
    purchase_id = AutoField()
    goods = ForeignKeyField(Goods, backref='purchases')
    channel = CharField(max_length=64) # 也可以单独建表
    buy_price = DecimalField(max_digits=10, decimal_places=2)
    buy_count = IntegerField()
    purchase_date = DateTimeField()
    
    class Meta: table_name = 'purchase_record'

# 4. 销售订单
class SalesOrder(BaseModel):
    order_id = AutoField()
    goods = ForeignKeyField(Goods, backref='sales')
    sale_price = DecimalField(max_digits=10, decimal_places=2)
    sale_count = IntegerField()
    platform_order_no = CharField(max_length=128, null=True, help_text='闲鱼单号')
    shipping_address = CharField(max_length=255, null=True)
    sale_date = DateTimeField()
    
    class Meta: table_name = 'sales_order'