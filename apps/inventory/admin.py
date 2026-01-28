from django.contrib import admin
from django.utils.html import format_html
from .models import Supplier, StockIn


# 自定义筛选器
class ProductCategoryFilter(admin.SimpleListFilter):
    title = '商品分类'
    parameter_name = 'product_category'
    
    def lookups(self, request, model_admin):
        from apps.products.models import Category
        categories = Category.objects.filter(parent__isnull=True)
        return [(c.id, c.name) for c in categories]
    
    def queryset(self, request, queryset):
        if self.value():
            from apps.products.models import Category
            category = Category.objects.get(id=self.value())
            # 包含该分类及其子分类的商品
            category_ids = [category.id] + list(category.children.values_list('id', flat=True))
            return queryset.filter(product__category_id__in=category_ids)


class HasSupplierFilter(admin.SimpleListFilter):
    title = '是否有供应商'
    parameter_name = 'has_supplier'
    
    def lookups(self, request, model_admin):
        return (
            ('yes', '有供应商'),
            ('no', '无供应商'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(supplier__isnull=False)
        elif self.value() == 'no':
            return queryset.filter(supplier__isnull=True)


class HasStockInFilter(admin.SimpleListFilter):
    title = '有无入库记录'
    parameter_name = 'has_stock_in'
    
    def lookups(self, request, model_admin):
        return (
            ('yes', '有入库记录'),
            ('no', '无入库记录'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(stock_ins__isnull=False).distinct()
        elif self.value() == 'no':
            return queryset.filter(stock_ins__isnull=True)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact', 'phone', 'is_active', 'stock_in_count', 'total_stock_in_amount', 'created_at']
    list_filter = ['is_active', HasStockInFilter, 'created_at']
    search_fields = ['name', 'contact', 'phone', 'address']
    list_editable = ['is_active']
    ordering = ['-created_at']
    list_per_page = 20
    
    def stock_in_count(self, obj):
        return obj.stock_ins.count()
    stock_in_count.short_description = '入库次数'
    
    def total_stock_in_amount(self, obj):
        from django.db.models import Sum, F
        result = obj.stock_ins.aggregate(total=Sum(F('quantity') * F('unit_cost')))
        total = result['total'] or 0
        return format_html('<b>{}</b>', f'{total:.2f}')
    total_stock_in_amount.short_description = '入库总额'


@admin.register(StockIn)
class StockInAdmin(admin.ModelAdmin):
    list_display = ['stock_in_no', 'product', 'product_category', 'quantity', 'unit_cost', 'total_cost',
                    'supplier', 'operator', 'created_at']
    list_filter = [ProductCategoryFilter, 'supplier', HasSupplierFilter, 'created_at']
    search_fields = ['stock_in_no', 'product__name', 'supplier__name', 'remark']
    ordering = ['-created_at']
    list_per_page = 20
    autocomplete_fields = ['product', 'supplier']
    readonly_fields = ['stock_in_no', 'operator', 'created_at']
    
    def product_category(self, obj):
        if obj.product.category:
            return obj.product.category.name
        return '-'
    product_category.short_description = '商品分类'
    
    fieldsets = (
        ('入库信息', {
            'fields': ('stock_in_no', 'product', 'quantity', 'unit_cost')
        }),
        ('其他信息', {
            'fields': ('supplier', 'remark', 'operator', 'created_at')
        }),
    )
    
    def total_cost(self, obj):
        unit_cost = obj.unit_cost or obj.product.cost_price
        return format_html('<b>{}</b>', f'{obj.quantity * unit_cost:.2f}')
    total_cost.short_description = '入库总成本'
    
    def unit_cost_display(self, obj):
        if obj.unit_cost:
            return obj.unit_cost
        return format_html('<span style="color: #999;">{}（商品成本）</span>', obj.product.cost_price)
    unit_cost_display.short_description = '单位成本'
    
    def save_model(self, request, obj, form, change):
        if not change:  # 新建时自动生成入库单号和设置操作人
            import time
            obj.stock_in_no = f'SI{int(time.time() * 1000)}'
            obj.operator = request.user
            # 如果未填写单位成本，使用商品成本价
            if obj.unit_cost is None:
                obj.unit_cost = obj.product.cost_price
        super().save_model(request, obj, form, change)
