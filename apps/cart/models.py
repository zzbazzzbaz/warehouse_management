from django.db import models
from django.conf import settings


class Cart(models.Model):
    """购物车"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='cart', verbose_name='用户'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'carts'
        verbose_name = '购物车'
        verbose_name_plural = '购物车'

    def __str__(self):
        return f'{self.user.username}的购物车'

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """购物车商品"""
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE,
        related_name='items', verbose_name='购物车'
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
        verbose_name = '购物车商品'
        verbose_name_plural = '购物车商品'
        unique_together = ['cart', 'product']

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    @property
    def subtotal(self):
        return self.product.selling_price * self.quantity
