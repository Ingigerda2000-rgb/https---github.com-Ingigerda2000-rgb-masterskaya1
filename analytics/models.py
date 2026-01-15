from django.db import models
from django.utils import timezone
from accounts.models import User

class DailyStat(models.Model):
    date = models.DateField('Дата', unique=True)
    
    # Продажи
    total_orders = models.IntegerField('Всего заказов', default=0)
    total_revenue = models.DecimalField('Выручка', max_digits=12, decimal_places=2, default=0)
    total_items_sold = models.IntegerField('Товаров продано', default=0)
    
    # Пользователи
    new_users = models.IntegerField('Новых пользователей', default=0)
    active_users = models.IntegerField('Активных пользователей', default=0)
    
    # Конверсия
    cart_abandonment_rate = models.DecimalField('Процент брошенных корзин', 
                                               max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Дневная статистика'
        verbose_name_plural = 'Дневная статистика'
        ordering = ['-date']
    
    def __str__(self):
        return f"Статистика за {self.date}"
    
    @classmethod
    def update_today_stats(cls):
        """Обновление статистики за сегодня"""
        today = timezone.now().date()
        stat, created = cls.objects.get_or_create(date=today)
        
        # Здесь будет логика обновления статистики
        # Пока просто сохраняем
        stat.save()
        return stat

class MasterStat(models.Model):
    master = models.ForeignKey(User, on_delete=models.CASCADE, 
                              limit_choices_to={'role': 'master'},
                              related_name='stats')
    period_start = models.DateField('Начало периода')
    period_end = models.DateField('Конец периода')
    
    # Продажи
    orders_count = models.IntegerField('Количество заказов', default=0)
    revenue = models.DecimalField('Выручка', max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField('Средний чек', max_digits=10, decimal_places=2, default=0)
    
    # Товары
    top_product = models.CharField('Топ товар', max_length=200, blank=True)
    top_product_sales = models.IntegerField('Продажи топ товара', default=0)
    
    # Материалы
    materials_cost = models.DecimalField('Стоимость материалов', max_digits=10, decimal_places=2, default=0)
    materials_used = models.TextField('Использованные материалы', blank=True)
    
    generated_at = models.DateTimeField('Сгенерировано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Статистика мастера'
        verbose_name_plural = 'Статистика мастеров'
        unique_together = ['master', 'period_start', 'period_end']
    
    def __str__(self):
        return f"Статистика {self.master.email} за {self.period_start} - {self.period_end}"
    
    def calculate_profit(self):
        """Расчет прибыли"""
        return self.revenue - self.materials_cost
    
    def calculate_margin(self):
        """Расчет маржинальности"""
        if self.revenue > 0:
            return ((self.revenue - self.materials_cost) / self.revenue) * 100
        return 0