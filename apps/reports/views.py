from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import timedelta

from apps.orders.models import Order
from apps.products.models import ProductStock
from apps.inventory.models import StockIn


def get_date_range(period='day', days=30):
    """根据周期获取日期范围"""
    end_date = timezone.now()
    if period == 'day':
        start_date = end_date - timedelta(days=days)
    elif period == 'week':
        start_date = end_date - timedelta(weeks=days)
    elif period == 'month':
        start_date = end_date - timedelta(days=days * 30)
    else:
        start_date = end_date - timedelta(days=30)
    return start_date, end_date


def get_trunc_func(period):
    """根据周期获取日期截断函数"""
    if period == 'week':
        return TruncWeek
    elif period == 'month':
        return TruncMonth
    return TruncDate


@staff_member_required
def sales_report_view(request):
    """销售报表页面"""
    return render(request, 'admin/reports/sales_report.html', {
        'title': '销售统计报表',
    })


@staff_member_required
def profit_report_view(request):
    """利润报表页面"""
    return render(request, 'admin/reports/profit_report.html', {
        'title': '利润分析报表',
    })


@staff_member_required
def inventory_report_view(request):
    """库存报表页面"""
    return render(request, 'admin/reports/inventory_report.html', {
        'title': '库存报表',
    })


@staff_member_required
def sales_trend_api(request):
    """销售额趋势数据API"""
    period = request.GET.get('period', 'day')
    days = int(request.GET.get('days', 30))

    start_date, end_date = get_date_range(period, days)
    trunc_func = get_trunc_func(period)

    # 查询已完成/已支付的订单
    orders = Order.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        status='completed'
    ).annotate(
        date=trunc_func('created_at')
    ).values('date').annotate(
        total_sales=Sum('total_amount'),
        order_count=Count('id')
    ).order_by('date')

    dates = []
    sales = []
    counts = []

    date_format = '%Y-%m' if period == 'month' else '%Y-%m-%d'
    for item in orders:
        dates.append(item['date'].strftime(date_format) if item['date'] else '')
        sales.append(float(item['total_sales'] or 0))
        counts.append(item['order_count'])

    return JsonResponse({
        'dates': dates,
        'sales': sales,
        'counts': counts
    })


@staff_member_required
def order_status_api(request):
    """订单状态分布数据API"""
    range_type = request.GET.get('range', 'today')  # today, month, year, all
    
    status_map = dict(Order.ORDER_STATUS)
    queryset = Order.objects.all()
    
    today = timezone.now().date()
    if range_type == 'today':
        queryset = queryset.filter(created_at__date=today)
    elif range_type == 'month':
        queryset = queryset.filter(created_at__date__gte=today.replace(day=1))
    elif range_type == 'year':
        queryset = queryset.filter(created_at__date__gte=today.replace(month=1, day=1))
    # 'all' 不需要过滤

    status_data = queryset.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    result = []
    for item in status_data:
        result.append({
            'name': status_map.get(item['status'], item['status']),
            'value': item['count']
        })

    return JsonResponse({'data': result})


@staff_member_required
def payment_method_api(request):
    """支付方式分布数据API"""
    range_type = request.GET.get('range', 'today')  # today, month, year, all
    
    method_map = dict(Order.PAYMENT_METHODS)
    queryset = Order.objects.filter(
        status='completed',
        payment_method__isnull=False
    )
    
    today = timezone.now().date()
    if range_type == 'today':
        queryset = queryset.filter(created_at__date=today)
    elif range_type == 'month':
        queryset = queryset.filter(created_at__date__gte=today.replace(day=1))
    elif range_type == 'year':
        queryset = queryset.filter(created_at__date__gte=today.replace(month=1, day=1))
    # 'all' 不需要过滤

    method_data = queryset.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('payment_method')

    result = []
    for item in method_data:
        result.append({
            'name': method_map.get(item['payment_method'], item['payment_method'] or '未知'),
            'count': item['count'],
            'total': float(item['total'] or 0)
        })

    return JsonResponse({'data': result})


@staff_member_required
def profit_trend_api(request):
    """利润趋势数据API"""
    period = request.GET.get('period', 'day')
    days = int(request.GET.get('days', 30))

    start_date, end_date = get_date_range(period, days)
    trunc_func = get_trunc_func(period)

    orders = Order.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        status='completed'
    ).annotate(
        date=trunc_func('created_at')
    ).values('date').annotate(
        total_sales=Sum('total_amount'),
        total_cost=Sum('total_cost')
    ).order_by('date')

    dates = []
    profits = []
    profit_rates = []
    sales = []
    costs = []

    date_format = '%Y-%m' if period == 'month' else '%Y-%m-%d'
    for item in orders:
        dates.append(item['date'].strftime(date_format) if item['date'] else '')
        total_sales = float(item['total_sales'] or 0)
        total_cost = float(item['total_cost'] or 0)
        profit = total_sales - total_cost

        sales.append(total_sales)
        costs.append(total_cost)
        profits.append(profit)

        # 毛利率
        if total_sales > 0:
            profit_rates.append(round(profit / total_sales * 100, 2))
        else:
            profit_rates.append(0)

    return JsonResponse({
        'dates': dates,
        'profits': profits,
        'profit_rates': profit_rates,
        'sales': sales,
        'costs': costs
    })


@staff_member_required
def profit_summary_api(request):
    """利润汇总数据API"""
    # 总体统计
    total_stats = Order.objects.filter(
        status='completed'
    ).aggregate(
        total_sales=Sum('total_amount'),
        total_cost=Sum('total_cost'),
        order_count=Count('id')
    )

    total_sales = float(total_stats['total_sales'] or 0)
    total_cost = float(total_stats['total_cost'] or 0)
    total_profit = total_sales - total_cost
    profit_rate = round(total_profit / total_sales * 100, 2) if total_sales > 0 else 0

    # 今日统计
    today = timezone.now().date()
    today_stats = Order.objects.filter(
        created_at__date=today,
        status='completed'
    ).aggregate(
        sales=Sum('total_amount'),
        cost=Sum('total_cost'),
        count=Count('id')
    )

    today_sales = float(today_stats['sales'] or 0)
    today_cost = float(today_stats['cost'] or 0)
    today_profit = today_sales - today_cost

    # 本月统计
    month_start = today.replace(day=1)
    month_stats = Order.objects.filter(
        created_at__date__gte=month_start,
        status='completed'
    ).aggregate(
        sales=Sum('total_amount'),
        cost=Sum('total_cost'),
        count=Count('id')
    )

    month_sales = float(month_stats['sales'] or 0)
    month_cost = float(month_stats['cost'] or 0)
    month_profit = month_sales - month_cost

    return JsonResponse({
        'total': {
            'sales': total_sales,
            'cost': total_cost,
            'profit': total_profit,
            'profit_rate': profit_rate,
            'order_count': total_stats['order_count'] or 0
        },
        'today': {
            'sales': today_sales,
            'cost': today_cost,
            'profit': today_profit,
            'count': today_stats['count'] or 0
        },
        'month': {
            'sales': month_sales,
            'cost': month_cost,
            'profit': month_profit,
            'count': month_stats['count'] or 0
        }
    })


@staff_member_required
def stock_status_api(request):
    """库存状态数据API"""
    stocks = ProductStock.objects.select_related('product', 'product__category').all()

    result = []
    for stock in stocks:
        result.append({
            'product_name': stock.product.name,
            'category': stock.product.category.name if stock.product.category else '未分类',
            'available': stock.available_quantity,
            'frozen': stock.frozen_quantity,
            'total': stock.total_quantity,
            'cost_price': float(stock.product.cost_price),
            'selling_price': float(stock.product.selling_price)
        })

    # 按分类统计
    category_stats = {}
    for item in result:
        cat = item['category']
        if cat not in category_stats:
            category_stats[cat] = {'total': 0, 'value': 0}
        category_stats[cat]['total'] += item['total']
        category_stats[cat]['value'] += item['total'] * item['cost_price']

    category_data = [{'name': k, 'total': v['total'], 'value': round(v['value'], 2)}
                     for k, v in category_stats.items()]

    return JsonResponse({
        'stocks': result,
        'category_stats': category_data
    })


@staff_member_required
def stock_in_trend_api(request):
    """入库趋势数据API"""
    period = request.GET.get('period', 'day')
    days = int(request.GET.get('days', 30))

    start_date, end_date = get_date_range(period, days)
    trunc_func = get_trunc_func(period)

    stock_ins = StockIn.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    ).annotate(
        date=trunc_func('created_at')
    ).values('date').annotate(
        total_quantity=Sum('quantity'),
        total_cost=Sum(F('quantity') * F('unit_cost')),
        record_count=Count('id')
    ).order_by('date')

    dates = []
    quantities = []
    costs = []
    counts = []

    date_format = '%Y-%m' if period == 'month' else '%Y-%m-%d'
    for item in stock_ins:
        dates.append(item['date'].strftime(date_format) if item['date'] else '')
        quantities.append(item['total_quantity'] or 0)
        costs.append(float(item['total_cost'] or 0))
        counts.append(item['record_count'])

    return JsonResponse({
        'dates': dates,
        'quantities': quantities,
        'costs': costs,
        'counts': counts
    })


@staff_member_required
def supplier_stats_api(request):
    """供应商统计数据API"""
    supplier_data = StockIn.objects.values(
        'supplier__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_cost=Sum(F('quantity') * F('unit_cost')),
        record_count=Count('id')
    ).order_by('-total_quantity')

    result = []
    for item in supplier_data:
        result.append({
            'name': item['supplier__name'] or '无供应商',
            'quantity': item['total_quantity'] or 0,
            'cost': float(item['total_cost'] or 0),
            'count': item['record_count']
        })

    return JsonResponse({'data': result})


@staff_member_required
def low_stock_api(request):
    """低库存预警数据API"""
    threshold = int(request.GET.get('threshold', 10))

    low_stocks = ProductStock.objects.select_related('product').filter(
        available_quantity__lte=threshold
    ).order_by('available_quantity')

    result = []
    for stock in low_stocks:
        result.append({
            'product_name': stock.product.name,
            'available': stock.available_quantity,
            'frozen': stock.frozen_quantity,
            'total': stock.total_quantity
        })

    return JsonResponse({'data': result})
