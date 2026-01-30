# materials/models.py - ПОЛНАЯ И ИСПРАВЛЕННАЯ ВЕРСИЯ
import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from accounts.models import User
from products.models import Product
from orders.models import OrderItem

class Material(models.Model):
    UNIT_CHOICES = [
        ('m', 'Метры'),
        ('cm', 'Сантиметры'),
        ('g', 'Граммы'),
        ('kg', 'Килограммы'),
        ('pcs', 'Штуки'),
        ('roll', 'Рулоны'),
        ('ml', 'Милилитры'),
        ('l', 'Лиры'),
        ('sheet', 'Листы'),
        ('pack', 'Упаковки'),
        ('spool', 'Катушки'),
    ]

    id = models.BigAutoField(primary_key=True)
    name = models.CharField('Название', max_length=100)
    master = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'master'},
        related_name='materials',
        verbose_name='Мастер'
    )
    
    # Количественные характеристики
    current_quantity = models.DecimalField(
        'Текущее количество', 
        max_digits=12, 
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Текущий остаток на складе'
    )
    unit = models.CharField(
        'Единица измерения', 
        max_length=10, 
        choices=UNIT_CHOICES,
        default='pcs'
    )
    min_quantity = models.DecimalField(
        'Минимальный запас', 
        max_digits=12, 
        decimal_places=3, 
        default=0,
        validators=[MinValueValidator(0)],
        help_text='При достижении этого количества будет показано предупреждение'
    )
    
    # Финансовые характеристики
    price_per_unit = models.DecimalField(
        'Цена за единицу', 
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Цена в рублях за одну единицу измерения'
    )
    last_purchase_price = models.DecimalField(
        'Последняя цена закупки', 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Цена последней закупки (для отслеживания изменений)'
    )
    
    # Технические характеристики
    color = models.CharField(
        'Цвет', 
        max_length=50, 
        blank=True,
        help_text='Основной цвет материала'
    )
    texture = models.CharField(
        'Текстура', 
        max_length=100, 
        blank=True,
        help_text='Текстура материала (гладкая, шероховатая и т.д.)'
    )
    supplier = models.CharField(
        'Поставщик', 
        max_length=200, 
        blank=True,
        help_text='Название компании-поставщика'
    )
    supplier_contact = models.CharField(
        'Контакты поставщика', 
        max_length=300, 
        blank=True,
        help_text='Телефон, email или сайт поставщика'
    )
    
    # Статус и системные поля
    is_active = models.BooleanField(
        'Активен', 
        default=True,
        help_text='Используется ли материал в производстве'
    )
    notes = models.TextField(
        'Примечания', 
        blank=True,
        help_text='Дополнительная информация о материале'
    )
    
    # Временные метки
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['master', 'name', 'color'],
                name='unique_material_per_master',
                condition=models.Q(is_active=True)
            )
        ]
        indexes = [
            models.Index(fields=['master', 'is_active']),
            models.Index(fields=['current_quantity']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.current_quantity} {self.get_unit_display()})"
    
    @property
    def is_low_stock(self):
        """Проверка на низкий запас"""
        return self.current_quantity > 0 and self.current_quantity <= self.min_quantity
    
    @property
    def stock_value(self):
        """Стоимость остатка на складе"""
        try:
            return self.current_quantity * self.price_per_unit
        except:
            return 0
    
    @property
    def available_quantity(self):
        """Доступное количество (исключая зарезервированное)"""
        try:
            reserved = self.reservations.filter(status='reserved').aggregate(
                total=models.Sum('quantity')
            )['total'] or 0
            return self.current_quantity - reserved
        except:
            return self.current_quantity
    
    def check_availability(self, required_quantity):
        """Проверка достаточности материала"""
        return self.available_quantity >= required_quantity
    
    def reserve(self, order_item, quantity):
        """Резервирование материала для заказа"""
        if not self.check_availability(quantity):
            raise ValueError(
                f"Недостаточно материала '{self.name}'. "
                f"Доступно: {self.available_quantity}, требуется: {quantity}"
            )
        
        reservation = MaterialReservation.objects.create(
            material=self,
            order_item=order_item,
            quantity=quantity,
            status='reserved'
        )
        return reservation
    
    def consume(self, reservation):
        """Списание материала"""
        if reservation.status != 'reserved':
            raise ValueError("Можно списать только зарезервированные материалы")
        
        # Уменьшаем текущее количество
        self.current_quantity -= reservation.quantity
        if self.current_quantity < 0:
            raise ValueError("Отрицательное количество материала")
        
        self.save()
        reservation.status = 'consumed'
        reservation.consumed_at = timezone.now()
        reservation.save()
        return True
    
    def release_reservation(self, reservation):
        """Освобождение резервирования"""
        if reservation.status != 'reserved':
            raise ValueError("Можно освободить только зарезервированные материалы")
        
        reservation.status = 'released'
        reservation.released_at = timezone.now()
        reservation.save()
        return True
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('materials:material_detail', kwargs={'pk': self.id})


class MaterialRecipe(models.Model):
    """Рецепт расхода материала на изделие"""
    id = models.BigAutoField(primary_key=True)
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='material_recipes',
        verbose_name='Товар'
    )
    material = models.ForeignKey(
        Material, 
        on_delete=models.CASCADE, 
        related_name='recipes',
        verbose_name='Материал'
    )
    
    # Нормы расхода
    consumption_rate = models.DecimalField(
        'Норма расхода', 
        max_digits=10, 
        decimal_places=3,
        validators=[MinValueValidator(0.001)],
        help_text='Сколько материала требуется для производства одной единицы изделия'
    )
    waste_factor = models.DecimalField(
        'Коэффициент отходов', 
        max_digits=5, 
        decimal_places=2, 
        default=0.10,
        validators=[MinValueValidator(0), MinValueValidator(1)],
        help_text='Процент отходов при производстве (0.1 = 10%)'
    )
    
    # Автоматизация
    auto_consume = models.BooleanField(
        'Автоматическое списание', 
        default=True,
        help_text='Автоматически списывать материал при производстве изделия'
    )
    
    # Примечания
    notes = models.TextField('Примечания', blank=True)
    
    class Meta:
        verbose_name = 'Рецепт материала'
        verbose_name_plural = 'Рецепты материалов'
        unique_together = ['product', 'material']
        ordering = ['material__name']
        indexes = [
            models.Index(fields=['product', 'material']),
        ]
    
    def __str__(self):
        return f"{self.product.name} → {self.material.name}: {self.consumption_rate}"
    
    def calculate_required(self, quantity=1, include_waste=True):
        """Рассчитать необходимое количество материала"""
        base_required = self.consumption_rate * quantity
        
        if include_waste:
            return base_required * (1 + self.waste_factor)
        return base_required
    
    def reserve_for_order(self, order_item, quantity):
        """Резервирование материала для конкретного заказа"""
        total_needed = self.calculate_required(quantity)
        return self.material.reserve(order_item, total_needed)
    
    def get_total_cost(self, quantity=1):
        """Стоимость материала для производства указанного количества изделия"""
        required = self.calculate_required(quantity)
        return required * self.material.price_per_unit


class MaterialReservation(models.Model):
    """Фиксация резервирования материала для заказа"""
    STATUS_CHOICES = [
        ('reserved', 'Зарезервировано'),
        ('consumed', 'Списано'),
        ('released', 'Освобождено'),
        ('cancelled', 'Отменено'),
    ]

    id = models.BigAutoField(primary_key=True)
    material = models.ForeignKey(
        Material, 
        on_delete=models.CASCADE, 
        related_name='reservations',
        verbose_name='Материал'
    )
    order_item = models.ForeignKey(
        OrderItem, 
        on_delete=models.CASCADE, 
        related_name='material_reservations',
        verbose_name='Позиция заказа',
        null=True,
        blank=True,
        help_text='Связь с позицией в заказе (если резервирование для заказа)'
    )
    
    quantity = models.DecimalField(
        'Количество', 
        max_digits=12, 
        decimal_places=3,
        validators=[MinValueValidator(0.001)],
        help_text='Зарезервированное количество'
    )
    status = models.CharField(
        'Статус', 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='reserved'
    )
    
    # Временные метки
    reserved_at = models.DateTimeField('Время резервирования', auto_now_add=True)
    consumed_at = models.DateTimeField('Время списания', null=True, blank=True)
    released_at = models.DateTimeField('Время освобождения', null=True, blank=True)
    
    # Примечания
    notes = models.TextField('Примечания', blank=True)
    
    class Meta:
        verbose_name = 'Резервирование материала'
        verbose_name_plural = 'Резервирования материалов'
        ordering = ['-reserved_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['reserved_at']),
            models.Index(fields=['material', 'status']),
            models.Index(fields=['order_item']),
        ]
    
    def __str__(self):
        if self.order_item:
            return f"Резерв {self.material.name} для заказа #{self.order_item.order.id if self.order_item.order else 'N/A'}"
        else:
            return f"Резерв {self.material.name} (ручное списание)"
    
    def consume(self):
        """Отметка о списании материала"""
        if self.status != 'reserved':
            raise ValueError("Можно списать только зарезервированные материалы")
        
        self.material.consume(self)
    
    def release(self):
        """Освобождение резерва"""
        if self.status != 'reserved':
            raise ValueError("Можно освободить только зарезервированные материалы")
        
        self.material.release_reservation(self)
    
    @property
    def cost(self):
        """Стоимость зарезервированного материала"""
        try:
            return self.quantity * self.material.price_per_unit
        except:
            return 0