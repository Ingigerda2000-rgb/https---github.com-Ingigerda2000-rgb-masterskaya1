from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from orders.models import Order, OrderItem
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def handle_order_status_change(sender, instance, **kwargs):
    """
    Автоматическое управление материалами при изменении статуса заказа
    """
    if not instance.pk:
        return  # Новый заказ, ещё не сохранён
    
    try:
        old_order = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        old_order = None
    
    # Если заказ только что создан (статус изменился на 'pending')
    if instance.status == 'pending' and (not old_order or old_order.status != 'pending'):
        try:
            with transaction.atomic():
                reservations = instance.reserve_materials()
                logger.info(f"Зарезервированы материалы для заказа #{instance.id}: {len(reservations)} резервирований")
        except Exception as e:
            logger.error(f"Ошибка резервирования материалов для заказа #{instance.id}: {e}")
            # Можно отправить уведомление мастеру
    
    # Если заказ переходит в производство
    elif instance.status == 'processing' and old_order and old_order.status != 'processing':
        try:
            with transaction.atomic():
                instance.consume_materials()
                logger.info(f"Списаны материалы для заказа #{instance.id}")
        except Exception as e:
            logger.error(f"Ошибка списания материалов для заказа #{instance.id}: {e}")
    
    # Если заказ отменён
    elif instance.status == 'cancelled' and old_order and old_order.status != 'cancelled':
        try:
            with transaction.atomic():
                for item in instance.items.all():
                    item.release_materials()
                logger.info(f"Освобождены материалы для отменённого заказа #{instance.id}")
        except Exception as e:
            logger.error(f"Ошибка освобождения материалов для заказа #{instance.id}: {e}")


@receiver(post_save, sender=OrderItem)
def handle_order_item_create(sender, instance, created, **kwargs):
    """
    Резервирование материалов при создании позиции заказа
    (если заказ уже в статусе pending)
    """
    if created and instance.order and instance.order.status == 'pending':
        try:
            with transaction.atomic():
                reservations = instance.reserve_materials()
                if reservations:
                    logger.info(f"Зарезервированы материалы для позиции #{instance.id}: {len(reservations)} резервирований")
        except Exception as e:
            logger.error(f"Ошибка резервирования материалов для позиции заказа #{instance.id}: {e}")


@receiver(pre_save, sender=OrderItem)
def handle_order_item_update(sender, instance, **kwargs):
    """
    Обновление резервирования при изменении количества в позиции заказа
    """
    if not instance.pk:
        return  # Новая позиция
    
    try:
        old_item = OrderItem.objects.get(pk=instance.pk)
        
        # Если изменилось количество изделий
        if old_item.quantity != instance.quantity and instance.order.status == 'pending':
            # Освобождаем старые резервирования
            old_item.release_materials()
            
            # Создаём новые резервирования
            instance.reserve_materials()
            
    except OrderItem.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Ошибка обновления резервирования для позиции #{instance.id}: {e}")