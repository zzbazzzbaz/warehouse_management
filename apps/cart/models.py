from django.db import models
from django.conf import settings


class CartItem(models.Model):
    """购物车项"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='cart_items', verbose_name='用户'
    )
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE,
        related_name='cart_items', verbose_name='商品'
    )
    quantity = models.IntegerField('数量', default=1)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'cart_items'
        verbose_name = '购物车'
        verbose_name_plural = '购物车'
        unique_together = ['user', 'product']

    def __str__(self):
        return f'{self.user.username} - {self.product.name}'

    @property
    def subtotal(self):
        return self.product.selling_price * self.quantity
