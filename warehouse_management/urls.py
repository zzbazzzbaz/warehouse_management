"""
URL configuration for warehouse_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 导入各应用的视图
from apps.users import views as users_views
from apps.products import views as products_views
from apps.cart import views as cart_views
from apps.orders import views as orders_views

# 配置管理站点标题
admin.site.site_header = '仓库管理系统'
admin.site.site_title = '仓库管理'
admin.site.index_title = '欢迎使用仓库管理系统'

urlpatterns = [
    path('admin/reports/', include('apps.reports.urls')),  # 必须在admin/之前
    path('admin/', admin.site.urls),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    
    # 认证
    path('login/', users_views.login_view, name='login'),
    path('logout/', users_views.logout_view, name='logout'),
    
    # 商品
    path('', products_views.product_list, name='product_list'),
    path('products/', products_views.product_list, name='products'),
    path('products/<int:pk>/', products_views.product_detail, name='product_detail'),
    
    # 购物车
    path('cart/', cart_views.cart_list, name='cart_list'),
    path('cart/add/', cart_views.cart_add, name='cart_add'),
    path('cart/update/', cart_views.cart_update, name='cart_update'),
    path('cart/remove/', cart_views.cart_remove, name='cart_remove'),
    
    # 订单
    path('orders/', orders_views.order_list, name='order_list'),
    path('orders/create/', orders_views.order_create, name='order_create'),
    path('orders/<int:pk>/', orders_views.order_detail, name='order_detail'),
    path('orders/<int:pk>/payment/', orders_views.order_payment, name='order_payment'),
    path('orders/<int:pk>/confirm-payment/', orders_views.order_confirm_payment, name='order_confirm_payment'),
    path('orders/<int:pk>/cancel/', orders_views.order_cancel, name='order_cancel'),
]

# 开发环境下服务媒体文件
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
