from peewee import CharField, IntegerField, DateTimeField, ForeignKeyField, DecimalField, AutoField
from ..conn import db
from .table_user import BaseModel
from .table_goods import Goods

# 3. 进货明细
class PurchaseRecord(BaseModel):
    purchase_id = AutoField()
    goods = ForeignKeyField(Goods, backref='purchases')
    channel = CharField(max_length=64) # 也可以单独建表
    buy_price = DecimalField(max_digits=10, decimal_places=2)
    buy_count = IntegerField()
    purchase_date = DateTimeField()
    
    class Meta: table_name = 'merchandise_purchase_record'

# 4. 销售订单
class SalesOrder(BaseModel):
    order_id = AutoField()
    goods = ForeignKeyField(Goods, backref='sales')
    sale_price = DecimalField(max_digits=10, decimal_places=2)
    sale_count = IntegerField()
    platform_order_no = CharField(max_length=128, null=True, help_text='闲鱼单号')
    shipping_address = CharField(max_length=255, null=True)
    sale_date = DateTimeField()
    
    class Meta: table_name = 'merchandise_sales_order'