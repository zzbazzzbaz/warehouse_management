from django.urls import path
from apps.users import views as users_views
from apps.products import views as products_views
from apps.cart import views as cart_views
from apps.orders import views as orders_views

app_name = 'frontend'

urlpatterns = [
    # 认证 (users)
    path('login/', users_views.login_view, name='login'),
    path('logout/', users_views.logout_view, name='logout'),
    
    # 商品 (products)
    path('', products_views.product_list, name='product_list'),
    path('products/', products_views.product_list, name='products'),
    path('products/<int:pk>/', products_views.product_detail, name='product_detail'),
    
    # 购物车 (cart)
    path('cart/', cart_views.cart_list, name='cart_list'),
    path('cart/add/', cart_views.cart_add, name='cart_add'),
    path('cart/update/', cart_views.cart_update, name='cart_update'),
    path('cart/remove/', cart_views.cart_remove, name='cart_remove'),
    
    # 订单 (orders)
    path('orders/', orders_views.order_list, name='order_list'),
    path('orders/create/', orders_views.order_create, name='order_create'),
    path('orders/<int:pk>/', orders_views.order_detail, name='order_detail'),
    path('orders/<int:pk>/payment/', orders_views.order_payment, name='order_payment'),
    path('orders/<int:pk>/confirm-payment/', orders_views.order_confirm_payment, name='order_confirm_payment'),
    path('orders/<int:pk>/cancel/', orders_views.order_cancel, name='order_cancel'),
]
