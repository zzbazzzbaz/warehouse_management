from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal
import uuid

from apps.products.models import Product, Category, ProductStock
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderItem, PaymentConfig, Payment


# ==================== 认证视图 ====================

def login_view(request):
    """用户登录"""
    if request.user.is_authenticated:
        return redirect('frontend:product_list')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'frontend:product_list')
            return redirect(next_url)
        else:
            messages.error(request, '用户名或密码错误')
    
    return render(request, 'frontend/login.html')


def logout_view(request):
    """用户登出"""
    logout(request)
    return redirect('frontend:login')


# ==================== 商品视图 ====================

@login_required(login_url='frontend:login')
def product_list(request):
    """商品列表"""
    products = Product.objects.filter(
        is_active=True,
        stock__available_quantity__gt=0  # 只显示有库存的商品
    ).select_related('category', 'stock')
    categories = Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('children')
    
    # 分类筛选
    category_id = request.GET.get('category')
    if category_id:
        # 包含子分类
        category = get_object_or_404(Category, id=category_id)
        if category.parent is None:
            # 一级分类，包含其下所有子分类
            child_ids = category.children.values_list('id', flat=True)
            products = products.filter(Q(category_id=category_id) | Q(category_id__in=child_ids))
        else:
            products = products.filter(category_id=category_id)
    
    # 搜索
    search = request.GET.get('search', '').strip()
    if search:
        products = products.filter(name__icontains=search)
    
    # 获取购物车数量
    cart_count = 0
    if hasattr(request.user, 'cart'):
        cart_count = request.user.cart.items.count()
    
    context = {
        'products': products,
        'categories': categories,
        'current_category': category_id,
        'search': search,
        'cart_count': cart_count,
    }
    return render(request, 'frontend/products/list.html', context)


@login_required(login_url='frontend:login')
def product_detail(request, pk):
    """商品详情"""
    product = get_object_or_404(
        Product.objects.select_related('category', 'stock'),
        pk=pk, is_active=True
    )
    
    # 获取购物车数量
    cart_count = 0
    if hasattr(request.user, 'cart'):
        cart_count = request.user.cart.items.count()
    
    context = {
        'product': product,
        'cart_count': cart_count,
    }
    return render(request, 'frontend/products/detail.html', context)


# ==================== 购物车视图 ====================

@login_required(login_url='frontend:login')
@require_POST
def cart_add(request):
    """加入购物车"""
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    
    # 获取或创建购物车
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    # 添加或更新购物车项
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    return JsonResponse({
        'success': True,
        'message': '已加入购物车',
        'cart_count': cart.items.count()
    })


@login_required(login_url='frontend:login')
def cart_list(request):
    """购物车列表"""
    cart = None
    items = []
    
    if hasattr(request.user, 'cart'):
        cart = request.user.cart
        items = cart.items.select_related('product', 'product__stock').all()
    
    context = {
        'cart': cart,
        'items': items,
        'cart_count': len(items),
    }
    return render(request, 'frontend/cart/list.html', context)


@login_required(login_url='frontend:login')
@require_POST
def cart_update(request):
    """更新购物车数量"""
    item_id = request.POST.get('item_id')
    quantity = int(request.POST.get('quantity', 1))
    
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    
    if quantity <= 0:
        item.delete()
        return JsonResponse({'success': True, 'message': '已删除', 'deleted': True})
    
    item.quantity = quantity
    item.save()
    
    cart = request.user.cart
    return JsonResponse({
        'success': True,
        'subtotal': float(item.subtotal),
        'total': float(cart.total_amount),
        'cart_count': cart.items.count()
    })


@login_required(login_url='frontend:login')
@require_POST
def cart_remove(request):
    """从购物车删除"""
    item_id = request.POST.get('item_id')
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    item.delete()
    
    cart_count = 0
    total = 0
    if hasattr(request.user, 'cart'):
        cart_count = request.user.cart.items.count()
        total = float(request.user.cart.total_amount)
    
    return JsonResponse({
        'success': True,
        'message': '已删除',
        'cart_count': cart_count,
        'total': total
    })


# ==================== 订单视图 ====================

@login_required(login_url='frontend:login')
@require_POST
def order_create(request):
    """创建订单"""
    item_ids = request.POST.getlist('item_ids')
    
    if not item_ids:
        messages.error(request, '请选择要结算的商品')
        return redirect('frontend:cart_list')
    
    cart_items = CartItem.objects.filter(
        id__in=item_ids,
        cart__user=request.user
    ).select_related('product', 'product__stock')
    
    if not cart_items.exists():
        messages.error(request, '未找到选中的商品')
        return redirect('frontend:cart_list')
    
    # 检查库存
    for item in cart_items:
        stock = getattr(item.product, 'stock', None)
        if not stock or stock.available_quantity < item.quantity:
            messages.error(request, f'商品 {item.product.name} 库存不足')
            return redirect('frontend:cart_list')
    
    with transaction.atomic():
        # 计算金额
        total_amount = sum(item.subtotal for item in cart_items)
        total_cost = sum(item.product.cost_price * item.quantity for item in cart_items)
        
        # 创建订单
        order = Order.objects.create(
            order_no=f'ORD{timezone.now().strftime("%Y%m%d%H%M%S")}{uuid.uuid4().hex[:6].upper()}',
            user=request.user,
            total_amount=total_amount,
            total_cost=total_cost,
            status='pending'
        )
        
        # 创建订单项并冻结库存
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.product.selling_price,
                cost_price=item.product.cost_price
            )
            
            # 冻结库存
            stock = item.product.stock
            stock.available_quantity -= item.quantity
            stock.frozen_quantity += item.quantity
            stock.save()
        
        # 删除购物车项
        cart_items.delete()
    
    return redirect('frontend:order_payment', pk=order.pk)


@login_required(login_url='frontend:login')
def order_list(request):
    """订单列表"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # 获取购物车数量
    cart_count = 0
    if hasattr(request.user, 'cart'):
        cart_count = request.user.cart.items.count()
    
    context = {
        'orders': orders,
        'cart_count': cart_count,
    }
    return render(request, 'frontend/orders/list.html', context)


@login_required(login_url='frontend:login')
def order_detail(request, pk):
    """订单详情"""
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        pk=pk, user=request.user
    )
    
    # 获取购物车数量
    cart_count = 0
    if hasattr(request.user, 'cart'):
        cart_count = request.user.cart.items.count()
    
    context = {
        'order': order,
        'cart_count': cart_count,
    }
    return render(request, 'frontend/orders/detail.html', context)


@login_required(login_url='frontend:login')
def order_payment(request, pk):
    """支付页面"""
    order = get_object_or_404(Order, pk=pk, user=request.user, status='pending')
    payment_configs = PaymentConfig.objects.filter(is_active=True)
    
    # 获取购物车数量
    cart_count = 0
    if hasattr(request.user, 'cart'):
        cart_count = request.user.cart.items.count()
    
    context = {
        'order': order,
        'payment_configs': payment_configs,
        'cart_count': cart_count,
    }
    return render(request, 'frontend/orders/payment.html', context)


@login_required(login_url='frontend:login')
@require_POST
def order_confirm_payment(request, pk):
    """确认支付完成"""
    order = get_object_or_404(Order, pk=pk, user=request.user, status='pending')
    payment_method = request.POST.get('payment_method', 'offline')
    
    with transaction.atomic():
        # 更新订单状态
        order.status = 'paid'
        order.payment_method = payment_method
        order.paid_at = timezone.now()
        order.save()
        
        # 创建支付记录
        Payment.objects.create(
            payment_no=f'PAY{timezone.now().strftime("%Y%m%d%H%M%S")}{uuid.uuid4().hex[:6].upper()}',
            order=order,
            amount=order.total_amount,
            payment_method='线下支付' if payment_method == 'offline' else '线上支付',
            status='success',
            operator=request.user,
            paid_at=timezone.now()
        )
        
        # 扣减冻结库存
        for item in order.items.all():
            stock = item.product.stock
            stock.frozen_quantity -= item.quantity
            stock.save()
    
    messages.success(request, '支付成功！')
    return redirect('frontend:order_detail', pk=order.pk)


@login_required(login_url='frontend:login')
@require_POST
def order_cancel(request, pk):
    """取消订单"""
    order = get_object_or_404(Order, pk=pk, user=request.user, status='pending')
    
    with transaction.atomic():
        # 释放冻结库存
        for item in order.items.all():
            stock = item.product.stock
            stock.available_quantity += item.quantity
            stock.frozen_quantity -= item.quantity
            stock.save()
        
        order.status = 'cancelled'
        order.save()
    
    messages.success(request, '订单已取消')
    return redirect('frontend:order_list')
