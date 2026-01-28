from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Order, Payment
from apps.products.models import ProductStock


@receiver(post_save, sender=Order)
def handle_order_stock(sender, instance, created, **kwargs):
    """
    订单创建时冻结库存
    """
    if created and instance.status == 'pending':
        with transaction.atomic():
            # 冻结订单中所有商品的库存
            for item in instance.items.all():
                stock, _ = ProductStock.objects.select_for_update().get_or_create(
                    product=item.product
                )
                # 检查库存是否足够
                if stock.available_quantity < item.quantity:
                    raise ValidationError(
                        f'商品 {item.product.name} 库存不足，可用库存：{stock.available_quantity}，需要：{item.quantity}'
                    )
                # 冻结库存
                stock.available_quantity -= item.quantity
                stock.frozen_quantity += item.quantity
                stock.save()


@receiver(pre_save, sender=Order)
def handle_order_status_change(sender, instance, **kwargs):
    """
    处理订单状态变化：
    - 取消订单时恢复库存
    - 支付订单时扣减冻结的库存
    """
    if instance.pk:  # 只处理已存在的订单
        try:
            old_order = Order.objects.get(pk=instance.pk)
            
            # 订单被取消，恢复库存
            if old_order.status != 'cancelled' and instance.status == 'cancelled':
                with transaction.atomic():
                    for item in instance.items.all():
                        stock = ProductStock.objects.select_for_update().get(
                            product=item.product
                        )
                        # 从冻结库存恢复到可用库存
                        stock.frozen_quantity -= item.quantity
                        stock.available_quantity += item.quantity
                        stock.save()
            
            # 订单支付成功，扣减库存
            elif old_order.status == 'pending' and instance.status == 'paid':
                with transaction.atomic():
                    for item in instance.items.all():
                        stock = ProductStock.objects.select_for_update().get(
                            product=item.product
                        )
                        # 扣减冻结库存（不增加可用库存）
                        stock.frozen_quantity -= item.quantity
                        stock.save()
        except Order.DoesNotExist:
            pass


@receiver(post_save, sender=Payment)
def handle_payment_success(sender, instance, created, **kwargs):
    """
    支付记录状态为成功时，自动更新订单状态为已支付
    """
    if instance.status == 'success':
        order = instance.order
        if order.status == 'pending':
            order.status = 'paid'
            order.paid_at = instance.paid_at
            order.save()
