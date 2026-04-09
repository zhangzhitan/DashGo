import dash
from dash.dependencies import Input, Output
from server import app
from database.sql_db.dao.dao_daily_statistics import get_daily_statistics
import plotly.graph_objects as go
import datetime

@app.callback(
    [Output('profit-stats-table', 'data'),
     Output('profit-stats-chart', 'figure')],
    [Input('profit-stats-date-range', 'value')]
)
def update_profit_stats(date_range):
    start_date, end_date = None, None
    if date_range:
        start_date = date_range[0]
        end_date = date_range[1]

    stats = get_daily_statistics(start_date=start_date, end_date=end_date)
    
    # Sort for chart (ascending by date)
    chart_stats = sorted(stats, key=lambda x: str(x['stat_date']))
    
    dates = [str(x['stat_date']) for x in chart_stats]
    income = [float(x['total_income']) for x in chart_stats]
    cost = [float(x['total_cost']) for x in chart_stats]
    profit_1 = [float(x['profit_1']) for x in chart_stats]
    profit_2 = [float(x['profit_2']) for x in chart_stats]

    fig = go.Figure()
    fig.add_trace(go.Bar(name='收入', x=dates, y=income))
    fig.add_trace(go.Bar(name='花费', x=dates, y=cost))
    fig.add_trace(go.Scatter(name='利润1', x=dates, y=profit_1, mode='lines+markers'))
    fig.add_trace(go.Scatter(name='利润2', x=dates, y=profit_2, mode='lines+markers'))
    
    fig.update_layout(
        barmode='group',
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Convert date to string for DataTable
    for row in stats:
        if isinstance(row['stat_date'], datetime.date):
            row['stat_date'] = row['stat_date'].strftime('%Y-%m-%d')
        elif not isinstance(row['stat_date'], str):
            row['stat_date'] = str(row['stat_date'])

    return stats, fig
