from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, PaymentConfig


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'unit_price', 'cost_price', 'subtotal_display', 'profit_display']
    can_delete = False
    
    def subtotal_display(self, obj):
        return f'{obj.subtotal:.2f}'
    subtotal_display.short_description = '小计'
    
    def profit_display(self, obj):
        return f'{obj.profit:.2f}'
    profit_display.short_description = '利润'
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_no', 'user', 'total_amount', 'total_cost', 'profit_display',
                    'status', 'payment_method', 'paid_at', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_no', 'user__username', 'user__phone']
    ordering = ['-created_at']
    list_per_page = 20
    readonly_fields = ['order_no', 'user', 'total_amount', 'total_cost', 'profit_display',
                       'shipping_address', 'remark', 'paid_at', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_completed', 'mark_as_cancelled']
    
    fieldsets = (
        ('订单信息', {
            'fields': ('order_no', 'user', 'status', 'payment_method')
        }),
        ('金额信息', {
            'fields': ('total_amount', 'total_cost', 'profit_display')
        }),
        ('其他信息', {
            'fields': ('shipping_address', 'remark', 'paid_at', 'created_at', 'updated_at')
        }),
    )
    
    def profit_display(self, obj):
        profit = obj.profit
        if profit > 0:
            return format_html('<span style="color: green;">{}</span>', f'+{profit:.2f}')
        elif profit < 0:
            return format_html('<span style="color: red;">{}</span>', f'{profit:.2f}')
        return '0.00'
    profit_display.short_description = '利润'
    
    @admin.action(description='标记为已支付')
    def mark_as_paid(self, request, queryset):
        from django.utils import timezone
        queryset.filter(status='pending').update(status='paid', paid_at=timezone.now())
    
    @admin.action(description='标记为已发货')
    def mark_as_shipped(self, request, queryset):
        queryset.filter(status='paid').update(status='shipped')
    
    @admin.action(description='标记为已完成')
    def mark_as_completed(self, request, queryset):
        queryset.filter(status='shipped').update(status='completed')
    
    @admin.action(description='标记为已取消')
    def mark_as_cancelled(self, request, queryset):
        queryset.filter(status__in=['pending', 'paid']).update(status='cancelled')


@admin.register(PaymentConfig)
class PaymentConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'qr_code_preview', 'is_active', 'sort_order', 'created_at']
    list_filter = ['is_active']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order']
    list_per_page = 20
    
    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;"/>', obj.qr_code.url)
        return '-'
    qr_code_preview.short_description = '收款码'
