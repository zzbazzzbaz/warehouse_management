from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # 报表页面
    path('sales/', views.sales_report_view, name='sales_report'),
    path('profit/', views.profit_report_view, name='profit_report'),
    path('inventory/', views.inventory_report_view, name='inventory_report'),
    
    # API接口
    path('api/sales-trend/', views.sales_trend_api, name='sales_trend_api'),
    path('api/order-status/', views.order_status_api, name='order_status_api'),
    path('api/payment-method/', views.payment_method_api, name='payment_method_api'),
    path('api/profit-trend/', views.profit_trend_api, name='profit_trend_api'),
    path('api/profit-summary/', views.profit_summary_api, name='profit_summary_api'),
    path('api/stock-status/', views.stock_status_api, name='stock_status_api'),
    path('api/stock-in-trend/', views.stock_in_trend_api, name='stock_in_trend_api'),
    path('api/supplier-stats/', views.supplier_stats_api, name='supplier_stats_api'),
    path('api/low-stock/', views.low_stock_api, name='low_stock_api'),
]
