from django.db import models
from django.conf import settings


class Supplier(models.Model):
    """供应商"""
    name = models.CharField('供应商名称', max_length=200)
    contact = models.CharField('联系人', max_length=100, blank=True)
    phone = models.CharField('联系电话', max_length=20, blank=True)
    address = models.TextField('地址', blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'suppliers'
        verbose_name = '供应商'
        verbose_name_plural = '供应商'

    def __str__(self):
        return self.name


class StockIn(models.Model):
    """入库记录"""
    stock_in_no = models.CharField('入库单号', max_length=50, unique=True)
    product = models.ForeignKey(
        'products.Product', on_delete=models.PROTECT,
        related_name='stock_ins', verbose_name='商品'
    )
    quantity = models.IntegerField('入库数量')
    unit_cost = models.DecimalField('单位成本', max_digits=10, decimal_places=2, null=True, blank=True, help_text='留空则使用商品成本价')
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL,
        null=True, related_name='stock_ins', verbose_name='供应商'
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='stock_in_records', verbose_name='操作人'
    )
    remark = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'stock_ins'
        verbose_name = '入库记录'
        verbose_name_plural = '入库记录'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['product']),
            models.Index(fields=['supplier']),
        ]

    def __str__(self):
        return f'{self.stock_in_no} - {self.product.name}'

