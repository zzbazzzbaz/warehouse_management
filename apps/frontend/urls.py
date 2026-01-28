from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    # 认证
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # 商品
    path('', views.product_list, name='product_list'),
    path('products/', views.product_list, name='products'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    
    # 购物车
    path('cart/', views.cart_list, name='cart_list'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    
    # 订单
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/payment/', views.order_payment, name='order_payment'),
    path('orders/<int:pk>/confirm-payment/', views.order_confirm_payment, name='order_confirm_payment'),
    path('orders/<int:pk>/cancel/', views.order_cancel, name='order_cancel'),
]
