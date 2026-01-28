from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, PaymentConfig, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    can_delete = True
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # 编辑时只读
            return ['product', 'quantity', 'unit_price', 'cost_price', 'subtotal_display', 'profit_display']
        return []  # 新增时可编辑
    
    def get_fields(self, request, obj=None):
        if obj:  # 编辑时显示所有字段
            return ['product', 'quantity', 'unit_price', 'cost_price', 'subtotal_display', 'profit_display']
        return ['product', 'quantity', 'unit_price', 'cost_price']  # 新增时
    
    def subtotal_display(self, obj):
        if obj.pk:
            return f'{obj.subtotal:.2f}'
        return '-'
    subtotal_display.short_description = '小计'
    
    def profit_display(self, obj):
        if obj.pk:
            return f'{obj.profit:.2f}'
        return '-'
    profit_display.short_description = '利润'
    
    def has_add_permission(self, request, obj=None):
        return obj is None  # 只在新增订单时允许添加商品


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_no', 'user', 'total_amount', 'total_cost', 'profit_display',
                    'status', 'payment_method', 'paid_at', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_no', 'user__username', 'user__phone']
    ordering = ['-created_at']
    list_per_page = 20
    inlines = [OrderItemInline]
    actions = None  # 禁用所有 actions
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # 编辑时
            return ['order_no', 'user', 'total_amount', 'total_cost', 'profit_display',
                    'remark', 'paid_at', 'created_at', 'updated_at']
        return ['order_no', 'user', 'total_amount', 'total_cost', 'profit_display',
                'paid_at', 'created_at', 'updated_at']  # 新增时备注可编辑
    
    def get_fieldsets(self, request, obj=None):
        if obj:  # 编辑时
            return (
                ('订单信息', {
                    'fields': ('order_no', 'user', 'status', 'payment_method')
                }),
                ('金额信息', {
                    'fields': ('total_amount', 'total_cost', 'profit_display')
                }),
                ('其他信息', {
                    'fields': ('remark', 'paid_at', 'created_at', 'updated_at')
                }),
            )
        # 新增时
        return (
            ('订单信息', {
                'fields': ('status', 'payment_method')
            }),
            ('其他信息', {
                'fields': ('remark',)
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
    
    @admin.action(description='标记为已完成')
    def mark_as_completed(self, request, queryset):
        queryset.filter(status='paid').update(status='completed')
    
    @admin.action(description='标记为已取消')
    def mark_as_cancelled(self, request, queryset):
        queryset.filter(status__in=['pending', 'paid']).update(status='cancelled')
    
    def has_add_permission(self, request):
        # 不允许添加订单
        return False
    
    def has_change_permission(self, request, obj=None):
        # 不允许修改订单
        return False
    
    def has_delete_permission(self, request, obj=None):
        # 不允许删除订单
        return False
    
    def save_model(self, request, obj, form, change):
        if not change:  # 新增时
            obj.user = request.user
            # 生成订单号
            import uuid
            from django.utils import timezone
            obj.order_no = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
            obj.total_amount = 0
            obj.total_cost = 0
        super().save_model(request, obj, form, change)
    
    def save_related(self, request, form, formsets, change):
        # 新增时，处理订单明细的默认值
        if not change:
            for formset in formsets:
                for item_form in formset.forms:
                    if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE'):
                        product = item_form.cleaned_data.get('product')
                        if product:
                            # 单价缺省时使用商品售价
                            if not item_form.cleaned_data.get('unit_price'):
                                item_form.instance.unit_price = product.selling_price
                            # 成本价缺省时使用商品成本价
                            if not item_form.cleaned_data.get('cost_price'):
                                item_form.instance.cost_price = product.cost_price
        
        super().save_related(request, form, formsets, change)
        
        if not change:  # 新增时计算总金额
            obj = form.instance
            total_amount = sum(item.subtotal for item in obj.items.all())
            total_cost = sum(item.cost_price * item.quantity for item in obj.items.all())
            obj.total_amount = total_amount
            obj.total_cost = total_cost
            obj.save(update_fields=['total_amount', 'total_cost'])


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


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_no', 'order', 'amount', 'payment_method', 'status', 'trade_no', 'operator', 'paid_at', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['payment_no', 'order__order_no', 'trade_no']
    ordering = ['-created_at']
    list_per_page = 20
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('payment_no', 'order', 'amount')
        }),
        ('支付信息', {
            'fields': ('payment_method', 'status', 'trade_no', 'paid_at')
        }),
        ('其他', {
            'fields': ('operator', 'remark', 'created_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # 新增时
            obj.operator = request.user
            # 生成支付单号
            import uuid
            from django.utils import timezone
            obj.payment_no = f"PAY{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # 编辑时
            return ['payment_no', 'order', 'amount', 'operator', 'created_at']
        return ['created_at']
    
    def has_add_permission(self, request):
        # 不允许添加支付记录
        return False
    
    def has_change_permission(self, request, obj=None):
        # 不允许修改支付记录
        return False
    
    def has_delete_permission(self, request, obj=None):
        # 不允许删除支付记录
        return False
