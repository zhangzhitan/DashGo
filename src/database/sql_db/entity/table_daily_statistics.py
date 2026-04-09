from peewee import IntegerField, DecimalField, DateField
from .table_user import BaseModel

class DailyStatistics(BaseModel):
    stat_date = DateField(unique=True, verbose_name="统计日期", help_text="统计的日期")
    
    total_in_count = IntegerField(default=0, verbose_name="当日进货总数", help_text="当日所有进货订单中商品数量之和")
    total_out_count = IntegerField(default=0, verbose_name="当日出货总数", help_text="当日所有销售订单中商品数量之和")
    
    total_cost = DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="当日总花费", help_text="当日所有进货单总额")
    total_income = DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="当日总收入", help_text="当日所有销售单总额")
    
    profit_1 = DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="利润1(收入-花费)", help_text="当日总收入减去当日总花费")
    profit_2 = DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="利润2", help_text="(当日售出商品价格 - 此商品历史平均进价) * 售出数量 之和")

    class Meta:
        table_name = 'merchandise_daily_statistics'
