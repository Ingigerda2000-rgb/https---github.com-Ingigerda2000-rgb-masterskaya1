from django.db import models
from accounts.models import User

class Notification(models.Model):
    TYPE_CHOICES = [
        ('order_status', 'Изменение статуса заказа'),
        ('new_order', 'Новый заказ'),
        ('low_stock', 'Низкий запас материалов'),
        ('review', 'Новый отзыв'),
        ('system', 'Системное уведомление'),
        ('promotion', 'Акция или предложение'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField('Тип уведомления', max_length=20, choices=TYPE_CHOICES)
    title = models.CharField('Заголовок', max_length=200)
    message = models.TextField('Сообщение')
    
    # Ссылка на связанный объект
    related_object_id = models.IntegerField('ID связанного объекта', null=True, blank=True)
    related_object_type = models.CharField('Тип объекта', max_length=50, blank=True)
    
    # Статус
    is_read = models.BooleanField('Прочитано', default=False)
    sent_via_email = models.BooleanField('Отправлено по email', default=False)
    sent_via_push = models.BooleanField('Отправлено как push', default=False)
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    read_at = models.DateTimeField('Дата прочтения', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()}: {self.title}"
    
    def mark_as_read(self):
        """Пометить как прочитанное"""
        if not self.is_read:
            self.is_read = True
            self.read_at = models.DateTimeField(auto_now=True)
            self.save()
    
    @classmethod
    def create_order_status_notification(cls, user, order, status_message):
        """Создать уведомление об изменении статуса заказа"""
        return cls.objects.create(
            user=user,
            notification_type='order_status',
            title=f"Статус заказа #{order.order_number} изменен",
            message=status_message,
            related_object_id=order.id,
            related_object_type='order'
        )