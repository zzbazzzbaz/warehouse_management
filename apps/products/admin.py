from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from .models import Category, Product, ProductStock


# 自定义筛选器
class HasImageFilter(admin.SimpleListFilter):
    title = '是否有图片'
    parameter_name = 'has_image'
    
    def lookups(self, request, model_admin):
        return (
            ('yes', '有图片'),
            ('no', '无图片'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(image='')
        elif self.value() == 'no':
            return queryset.filter(image='')


class CategoryLevelFilter(admin.SimpleListFilter):
    title = '分类级别'
    parameter_name = 'level'
    
    def lookups(self, request, model_admin):
        return (
            ('root', '顶级分类'),
            ('sub', '子分类'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'root':
            return queryset.filter(parent__isnull=True)
        elif self.value() == 'sub':
            return queryset.filter(parent__isnull=False)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'sort_order', 'is_active', 'product_count', 'created_at']
    list_filter = [CategoryLevelFilter, 'is_active', 'created_at']
    search_fields = ['name']
    list_editable = ['sort_order', 'is_active']
    ordering = ['sort_order', 'id']
    list_per_page = 20
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = '商品数'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """父分类只能选择顶级分类（限制二级）"""
        if db_field.name == 'parent':
            kwargs['queryset'] = Category.objects.filter(parent__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('tree/', self.admin_site.admin_view(self.category_tree_view), name='products_category_tree'),
        ]
        return custom_urls + urls
    
    def category_tree_view(self, request):
        # 获取所有顶级分类
        root_categories = Category.objects.filter(parent__isnull=True).order_by('sort_order')
        
        # 为每个分类添加商品数量和子分类（最多二级）
        def get_category_with_children(category):
            category.product_count = category.products.count()
            category.children_list = []
            for child in category.children.all().order_by('sort_order'):
                child.product_count = child.products.count()
                category.children_list.append(child)
            return category
        
        categories = [get_category_with_children(cat) for cat in root_categories]
        
        context = {
            **self.admin_site.each_context(request),
            'title': '商品分类树',
            'categories': categories,
            'total_categories': Category.objects.count(),
            'total_products': Product.objects.count(),
        }
        return render(request, 'admin/products/category_tree.html', context)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'cost_price', 'selling_price', 'is_active', 'image_preview', 'created_at']
    list_filter = ['category', 'is_active', HasImageFilter, 'created_at']
    search_fields = ['name', 'description', 'category__name']
    list_editable = ['is_active']
    ordering = ['-created_at']
    list_per_page = 20
    readonly_fields = ['image_preview_large', 'created_at', 'updated_at']
    
    def profit_display(self, obj):
        profit = obj.selling_price - obj.cost_price
        rate = (profit / obj.cost_price * 100) if obj.cost_price else 0
        color = 'green' if rate >= 20 else 'orange' if rate >= 10 else 'red'
        return format_html('<span style="color: {};">{}</span>', color, f'{rate:.0f}%')
    profit_display.short_description = '利润率'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'category', 'description', 'image', 'image_preview_large')
        }),
        ('价格信息', {
            'fields': ('cost_price', 'selling_price')
        }),
        ('状态', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;"/>', obj.image.url)
        return '-'
    image_preview.short_description = '图片'
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="200" style="max-height: 200px; object-fit: contain;"/>', obj.image.url)
        return '暂无图片'
    image_preview_large.short_description = '图片预览'


@admin.register(ProductStock)
class ProductStockAdmin(admin.ModelAdmin):
    list_display = ['product', 'available_quantity', 'frozen_quantity', 'total_quantity_display', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['product__name']
    ordering = ['-updated_at']
    list_per_page = 20
    readonly_fields = ['product', 'updated_at']
    
    def total_quantity_display(self, obj):
        return obj.total_quantity
    total_quantity_display.short_description = '总库存'
    
    def has_add_permission(self, request):
        # 不允许手动添加，通过入库自动创建
        return False
    
    def has_change_permission(self, request, obj=None):
        # 不允许修改库存记录
        return False
    
    def has_delete_permission(self, request, obj=None):
        # 不允许删除库存记录
        return False
