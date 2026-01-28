from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import StockIn
from apps.products.models import ProductStock


@receiver(post_save, sender=StockIn)
def update_stock_on_stock_in(sender, instance, created, **kwargs):
    """入库后自动增加商品库存"""
    if created:  # 只在新创建时处理
        with transaction.atomic():
            # 获取或创建商品库存记录
            stock, _ = ProductStock.objects.select_for_update().get_or_create(
                product=instance.product
            )
            # 增加可用库存
            stock.available_quantity += instance.quantity
            stock.save()
