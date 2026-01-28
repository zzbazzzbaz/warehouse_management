from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Cart, CartItem
from apps.products.models import Product


# ==================== 前台视图 ====================

@login_required(login_url='login')
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


@login_required(login_url='login')
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


@login_required(login_url='login')
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


@login_required(login_url='login')
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
