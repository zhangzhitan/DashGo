from peewee import CharField, IntegerField, ForeignKeyField, DecimalField, AutoField, DateTimeField
from .table_user import BaseModel
from .table_goods import Goods

# 1. 进出货渠道（如：闲鱼、淘宝、线下展会等）
class DimChannel(BaseModel):
    channel_name = CharField(primary_key=True)
    channel_remark = CharField(max_length=128, null=True)
    class Meta: table_name = 'merchandise_dim_channel'

# 订单状态常量枚举
class OrderStatus:
    PRESALE = '预售'
    PENDING_SHIP = '待发货'
    PENDING_RECEIPT = '待收货'
    RETURNED = '退货'
    COMPLETED = '已完成'

# ================= 销售/出货模块 =================

# 2. 出货主表 (Sales Order)
class SalesOrder(BaseModel):
    order_id = AutoField()
    # 外部ID，比如闲鱼的订单号
    external_order_no = CharField(max_length=128, unique=True, help_text='外部单号')
    channel = ForeignKeyField(DimChannel, backref='sales_orders')
    order_status = CharField(max_length=32, default=OrderStatus.PENDING_SHIP)
    
    total_amount = DecimalField(max_digits=12, decimal_places=2, default=0, help_text='订单总价')
    shipping_address = CharField(max_length=255, null=True, help_text='收货信息')
    order_date = DateTimeField()
    
    class Meta: table_name = 'merchandise_sales_order'

# 3. 出货明细表 (Sales Order Detail)
class SalesOrderDetail(BaseModel):
    detail_id = AutoField()
    # 级联删除，主订单删了明细也跟着删
    order = ForeignKeyField(SalesOrder, backref='details', on_delete='CASCADE')
    goods = ForeignKeyField(Goods, backref='sales_details')
    
    sale_price = DecimalField(max_digits=10, decimal_places=2, help_text='售出单价')
    sale_count = IntegerField(help_text='售出数量')
    subtotal = DecimalField(max_digits=12, decimal_places=2, help_text='小计')
    
    class Meta: table_name = 'merchandise_sales_order_detail'


# ================= 进货/入库模块 =================

class PurchaseOrder(BaseModel):
    order_id = AutoField()
    # 外部ID，比如淘宝/拼多多的购买单号
    external_order_no = CharField(max_length=128, unique=True, help_text='外部单号')
    channel = ForeignKeyField(DimChannel, backref='purchase_orders')
    
    # 进货状态
    order_status = CharField(max_length=32, default='已下单')
    total_amount = DecimalField(max_digits=12, decimal_places=2, default=0, help_text='进货总价')
    remark = CharField(max_length=255, null=True, help_text='备注(如物流单号/供应商)')
    order_date = DateTimeField()
    
    class Meta: table_name = 'merchandise_purchase_order'

class PurchaseOrderDetail(BaseModel):
    detail_id = AutoField()
    order = ForeignKeyField(PurchaseOrder, backref='details', on_delete='CASCADE')
    goods = ForeignKeyField(Goods, backref='purchase_details')
    
    buy_price = DecimalField(max_digits=10, decimal_places=2, help_text='进货单价')
    buy_count = IntegerField(help_text='进货数量')
    subtotal = DecimalField(max_digits=12, decimal_places=2, help_text='小计')
    
    class Meta: table_name = 'merchandise_purchase_order_detail'