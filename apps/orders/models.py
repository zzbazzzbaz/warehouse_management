from django.db import models
from django.conf import settings


class Order(models.Model):
    """订单"""
    ORDER_STATUS = [
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    PAYMENT_METHODS = [
        ('offline', '线下支付'),
        ('online', '线上支付'),
    ]

    order_no = models.CharField('订单号', max_length=50, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='orders', verbose_name='用户'
    )
    total_amount = models.DecimalField('订单金额', max_digits=10, decimal_places=2)
    total_cost = models.DecimalField('总成本', max_digits=10, decimal_places=2)
    status = models.CharField('订单状态', max_length=20, choices=ORDER_STATUS, default='pending')
    payment_method = models.CharField(
        '支付方式', max_length=20, choices=PAYMENT_METHODS,
        null=True, blank=True
    )
    shipping_address = models.TextField('收货地址', blank=True)
    remark = models.TextField('备注', blank=True)
    paid_at = models.DateTimeField('支付时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'orders'
        verbose_name = '订单'
        verbose_name_plural = '订单'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.order_no

    @property
    def profit(self):
        return self.total_amount - self.total_cost


class OrderItem(models.Model):
    """订单明细"""
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='items', verbose_name='订单'
    )
    product = models.ForeignKey(
        'products.Product', on_delete=models.PROTECT,
        related_name='order_items', verbose_name='商品'
    )
    quantity = models.IntegerField('数量')
    unit_price = models.DecimalField('单价', max_digits=10, decimal_places=2)
    cost_price = models.DecimalField('成本价', max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_items'
        verbose_name = '订单明细'
        verbose_name_plural = '订单明细'

    def __str__(self):
        return f'{self.order.order_no} - {self.product.name}'

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    @property
    def profit(self):
        return (self.unit_price - self.cost_price) * self.quantity


class PaymentConfig(models.Model):
    """支付配置"""
    name = models.CharField('支付方式名称', max_length=100)
    qr_code = models.ImageField('收款码', upload_to='payment/')
    is_active = models.BooleanField('是否启用', default=True)
    sort_order = models.IntegerField('排序', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'payment_configs'
        verbose_name = '支付配置'
        verbose_name_plural = '支付配置'
        ordering = ['sort_order']

    def __str__(self):
        return self.name
