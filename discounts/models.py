from django.db import models
from django.utils import timezone
from accounts.models import User

class PromoCode(models.Model):
    """Модель промокода"""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Процент'),
        ('fixed', 'Фиксированная сумма'),
    ]
    
    code = models.CharField('Код', max_length=50, unique=True)
    discount_type = models.CharField('Тип скидки', max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField('Значение скидки', max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField('Минимальная сумма заказа', max_digits=10, decimal_places=2, default=0)
    max_uses = models.IntegerField('Максимальное количество использований', default=1)
    used_count = models.IntegerField('Использовано раз', default=0)
    is_active = models.BooleanField('Активен', default=True)
    valid_from = models.DateTimeField('Действует с', default=timezone.now)
    valid_to = models.DateTimeField('Действует до', null=True, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
    
    def __str__(self):
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percentage' else '₽'}"
    
    def is_valid(self, order_amount=None):
        """Проверка валидности промокода"""
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.valid_to and now > self.valid_to:
            return False
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if order_amount and self.min_order_amount > 0 and order_amount < self.min_order_amount:
            return False
        
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        
        return True
    
    def calculate_discount(self, order_amount):
        """Расчёт суммы скидки"""
        if not self.is_valid(order_amount):
            return 0
        
        if self.discount_type == 'percentage':
            discount = (order_amount * self.discount_value) / 100
        else:  # fixed
            discount = min(self.discount_value, order_amount)
        
        return discount

class Discount(models.Model):
    """Скидка на заказ"""
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='discount')
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='discounts')
    discount_amount = models.DecimalField('Сумма скидки', max_digits=10, decimal_places=2)
    discount_reason = models.CharField('Причина скидки', max_length=200, blank=True)
    
    class Meta:
        verbose_name = 'Скидка'
        verbose_name_plural = 'Скидки'
    
    def __str__(self):
        return f"Скидка {self.discount_amount}₽ для заказа #{self.order.order_number}"