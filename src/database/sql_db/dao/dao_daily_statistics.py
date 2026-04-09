import datetime
from peewee import fn
from database.sql_db.conn import db
from database.sql_db.entity.table_inventory import PurchaseOrder, PurchaseOrderDetail, SalesOrder, SalesOrderDetail
from database.sql_db.entity.table_daily_statistics import DailyStatistics

def calculate_and_save_daily_statistics(target_date: datetime.date = None):
    # If None, default to yesterday
    if target_date is None:
        target_date = datetime.date.today() - datetime.timedelta(days=1)
        
    start_dt = datetime.datetime.combine(target_date, datetime.time.min)
    end_dt = start_dt + datetime.timedelta(days=1)
    
    with db().atomic():
        # 1. Inbound count and Total Cost
        cost_query = PurchaseOrder.select(fn.SUM(PurchaseOrder.total_amount)).where(
            PurchaseOrder.order_date >= start_dt,
            PurchaseOrder.order_date < end_dt
        ).scalar()
        total_cost = cost_query if cost_query else 0
        
        in_count_query = PurchaseOrderDetail.select(fn.SUM(PurchaseOrderDetail.buy_count)).join(
            PurchaseOrder
        ).where(
            PurchaseOrder.order_date >= start_dt,
            PurchaseOrder.order_date < end_dt
        ).scalar()
        total_in_count = in_count_query if in_count_query else 0
        
        # 2. Outbound count and Total Income
        income_query = SalesOrder.select(fn.SUM(SalesOrder.total_amount)).where(
            SalesOrder.order_date >= start_dt,
            SalesOrder.order_date < end_dt
        ).scalar()
        total_income = income_query if income_query else 0
        
        out_count_query = SalesOrderDetail.select(fn.SUM(SalesOrderDetail.sale_count)).join(
            SalesOrder
        ).where(
            SalesOrder.order_date >= start_dt,
            SalesOrder.order_date < end_dt
        ).scalar()
        total_out_count = out_count_query if out_count_query else 0
        
        profit_1 = total_income - total_cost
        
        # 3. Calculate profit_2
        # For each sold item on target_date, find the historical avg buy_price.
        sold_items = SalesOrderDetail.select(
            SalesOrderDetail.goods_id,
            fn.SUM(SalesOrderDetail.sale_count).alias('qty_sold'),
            fn.SUM(SalesOrderDetail.subtotal).alias('total_sale_value')
        ).join(SalesOrder).where(
            SalesOrder.order_date >= start_dt,
            SalesOrder.order_date < end_dt
        ).group_by(SalesOrderDetail.goods_id).dicts()
        
        profit_2 = 0
        for item in sold_items:
            goods_id = item['goods']
            qty_sold = item['qty_sold']
            total_sale_value = item['total_sale_value']
            
            # historic avg buy price
            historic_purchases = PurchaseOrderDetail.select(
                fn.SUM(PurchaseOrderDetail.buy_count).alias('total_buy'),
                fn.SUM(PurchaseOrderDetail.subtotal).alias('total_spent')
            ).join(PurchaseOrder).where(
                PurchaseOrderDetail.goods_id == goods_id,
                PurchaseOrder.order_date < end_dt
            ).dicts()
            
            historic_row = list(historic_purchases)[0] if historic_purchases else None
            
            if historic_row and historic_row['total_buy'] and historic_row['total_spent']:
                avg_buy_price = historic_row['total_spent'] / historic_row['total_buy']
            else:
                avg_buy_price = 0
            
            profit_2 += total_sale_value - (avg_buy_price * qty_sold)
            
        # 4. Save to DB
        stat_entry, created = DailyStatistics.get_or_create(
            stat_date=target_date,
            defaults={
                'total_in_count': total_in_count,
                'total_out_count': total_out_count,
                'total_cost': total_cost,
                'total_income': total_income,
                'profit_1': profit_1,
                'profit_2': profit_2
            }
        )
        if not created:
            stat_entry.total_in_count = total_in_count
            stat_entry.total_out_count = total_out_count
            stat_entry.total_cost = total_cost
            stat_entry.total_income = total_income
            stat_entry.profit_1 = profit_1
            stat_entry.profit_2 = profit_2
            stat_entry.save()
            
def get_daily_statistics(start_date=None, end_date=None):
    query = DailyStatistics.select().order_by(DailyStatistics.stat_date.desc())
    if start_date:
        query = query.where(DailyStatistics.stat_date >= start_date)
    if end_date:
        query = query.where(DailyStatistics.stat_date <= end_date)
    return list(query.dicts())
