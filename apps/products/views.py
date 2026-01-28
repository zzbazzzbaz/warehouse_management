from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .models import Product, Category


# ==================== 前台视图 ====================

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
