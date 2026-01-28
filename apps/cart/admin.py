from django.contrib import admin
from django.utils.html import format_html
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ['subtotal_display']
    autocomplete_fields = ['product']
    
    def subtotal_display(self, obj):
        if obj.pk:
            return f'{obj.subtotal:.2f}'
        return '-'
    subtotal_display.short_description = '小计'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'item_count', 'total_quantity_display', 'total_amount_display', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__phone']
    ordering = ['-updated_at']
    list_per_page = 20
    autocomplete_fields = ['user']
    inlines = [CartItemInline]
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = '商品种类'
    
    def total_quantity_display(self, obj):
        return obj.total_quantity
    total_quantity_display.short_description = '商品总数'
    
    def total_amount_display(self, obj):
        return format_html('<b>{}</b>', f'{obj.total_amount:.2f}')
    total_amount_display.short_description = '总金额'
    
    def has_add_permission(self, request):
        # 不允许添加购物车
        return False
    
    def has_change_permission(self, request, obj=None):
        # 不允许修改购物车
        return False
    
    def has_delete_permission(self, request, obj=None):
        # 不允许删除购物车
        return False
