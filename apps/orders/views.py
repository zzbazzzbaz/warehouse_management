from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
import uuid

from .models import Order, OrderItem, PaymentConfig, Payment
from apps.cart.models import CartItem
from apps.products.models import ProductStock
from apps.inventory.services import check_cart_items_stock, InsufficientStockError


# ==================== 前台视图 ====================

@login_required(login_url='login')
@require_POST
def order_create(request):
    """创建订单"""
    item_ids = request.POST.getlist('item_ids')
    
    if not item_ids:
        messages.error(request, '请选择要结算的商品')
        return redirect('cart_list')
    
    cart_items = CartItem.objects.filter(
        id__in=item_ids,
        cart__user=request.user
    ).select_related('product', 'product__stock')
    
    if not cart_items.exists():
        messages.error(request, '未找到选中的商品')
        return redirect('cart_list')
    
    # 检查库存
    try:
        check_cart_items_stock(cart_items)
    except InsufficientStockError as e:
        messages.error(request, str(e))
        return redirect('cart_list')
    
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
            
            # 冻结库存（从可用库存转移到冻结库存）
            stock = ProductStock.objects.select_for_update().get(product=item.product)
            stock.available_quantity -= item.quantity
            stock.frozen_quantity += item.quantity
            stock.save()
        
        # 删除购物车项
        cart_items.delete()
    
    return redirect('order_payment', pk=order.pk)


@login_required(login_url='login')
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


@login_required(login_url='login')
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


@login_required(login_url='login')
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


@login_required(login_url='login')
@require_POST
def order_confirm_payment(request, pk):
    """确认支付完成"""
    order = get_object_or_404(Order, pk=pk, user=request.user, status='pending')
    payment_method = request.POST.get('payment_method', 'offline')
    
    with transaction.atomic():
        # 更新订单状态（库存由 signal 统一处理）
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
    
    messages.success(request, '支付成功！')
    return redirect('order_detail', pk=order.pk)


@login_required(login_url='login')
@require_POST
def order_cancel(request, pk):
    """取消订单"""
    order = get_object_or_404(Order, pk=pk, user=request.user, status='pending')
    
    with transaction.atomic():
        # 更新订单状态（库存由 signal 统一处理）
        order.status = 'cancelled'
        order.save()
    
    messages.success(request, '订单已取消')
    return redirect('order_list')
