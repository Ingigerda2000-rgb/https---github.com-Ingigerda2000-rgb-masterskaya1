from django.db import models
from accounts.models import User
from products.models import Product

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачен'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField('Номер заказа', max_length=20, unique=True)
    total_amount = models.DecimalField('Общая сумма', max_digits=10, decimal_places=2)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Данные доставки
    delivery_address = models.TextField('Адрес доставки')
    customer_name = models.CharField('Имя получателя', max_length=100)
    customer_phone = models.CharField('Телефон', max_length=20)
    customer_email = models.EmailField('Email')
    
    # Доставка
    delivery_cost = models.DecimalField('Стоимость доставки', max_digits=10, decimal_places=2, default=0)
    delivery_method = models.CharField('Способ доставки', max_length=50, blank=True)
    tracking_number = models.CharField('Трек-номер', max_length=100, blank=True)
    
    # Оплата
    payment_method = models.CharField('Способ оплаты', max_length=50, blank=True)
    payment_id = models.CharField('ID платежа', max_length=100, blank=True)
    paid_at = models.DateTimeField('Дата оплаты', null=True, blank=True)
    
    # Скидки
    discount_amount = models.DecimalField('Сумма скидки', max_digits=10, decimal_places=2, default=0)
    promo_code = models.CharField('Промокод', max_length=50, blank=True)
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Заказ #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Генерация номера заказа: ГОД-МЕСЯЦ-ПОСЛЕДОВАТЕЛЬНЫЙ НОМЕР
            from django.utils import timezone
            import random
            year_month = timezone.now().strftime('%Y%m')
            last_order = Order.objects.filter(order_number__startswith=year_month).order_by('-id').first()
            if last_order:
                last_num = int(last_order.order_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.order_number = f"{year_month}-{new_num:04d}"
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """Пересчет общей суммы заказа"""
        items_total = sum(item.calculate_subtotal() for item in self.items.all())
        total = items_total + self.delivery_cost - self.discount_amount
        return total

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.IntegerField('Количество')
    price = models.DecimalField('Цена за единицу', max_digits=10, decimal_places=2)
    product_name = models.CharField('Название товара', max_length=200)
    
    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
    
    def calculate_subtotal(self):
        return self.price * self.quantity

class OrderStatusHistory(models.Model):
    STATUS_CHOICES = [
        ('accepted', 'ПРИНЯТ'),
        ('agreed', 'СОГЛАСОВАН'),
        ('in_production', 'В РАБОТЕ'),
        ('preparing_for_shipment', 'ГОТОВИТСЯ К ОТПРАВКЕ'),
        ('shipped', 'ОТПРАВЛЕН'),
        ('delivered', 'ДОСТАВЛЕН'),
        ('cancelled', 'ОТМЕНЁН'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField('Статус', max_length=50, choices=STATUS_CHOICES)
    stage_detail = models.TextField('Детализация этапа', blank=True)
    comment = models.TextField('Комментарий', blank=True)
    photo = models.ImageField('Фотоотчёт', upload_to='order_status/', blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='changed_orders')
    changed_at = models.DateTimeField('Время изменения', auto_now_add=True)
    notify_customer = models.BooleanField('Уведомить покупателя', default=True)
    
    class Meta:
        verbose_name = 'История статуса заказа'
        verbose_name_plural = 'История статусов заказов'
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.get_status_display()}"