# materials/models.py
from django.db import models
from accounts.models import User

class Material(models.Model):
    UNIT_CHOICES = [
        ('m', 'Метры'),
        ('cm', 'Сантиметры'),
        ('g', 'Граммы'),
        ('kg', 'Килограммы'),
        ('pcs', 'Штуки'),
        ('roll', 'Рулоны'),
    ]
    
    name = models.CharField('Название', max_length=100)
    master = models.ForeignKey(User, on_delete=models.CASCADE, 
                              limit_choices_to={'role': 'master'},
                              related_name='materials')
    current_quantity = models.DecimalField('Текущее количество', max_digits=12, decimal_places=3)
    unit = models.CharField('Единица измерения', max_length=10, choices=UNIT_CHOICES)
    min_quantity = models.DecimalField('Минимальный запас', max_digits=12, decimal_places=3, default=0)
    price_per_unit = models.DecimalField('Цена за единицу', max_digits=10, decimal_places=2, default=0)
    
    # Дополнительные поля
    color = models.CharField('Цвет', max_length=50, blank=True)
    texture = models.CharField('Текстура', max_length=100, blank=True)
    supplier = models.CharField('Поставщик', max_length=200, blank=True)
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.current_quantity} {self.get_unit_display()})"
    
    def is_low_stock(self):
        """Проверка на низкий запас"""
        return self.current_quantity <= self.min_quantity
    
    def check_availability(self, required_quantity):
        """Проверка достаточности материала"""
        return self.current_quantity >= required_quantity
    
    def reserve(self, quantity, order_id):
        """Резервирование материала для заказа"""
        if self.check_availability(quantity):
            # Создаем запись о резервировании
            reservation = MaterialReservation.objects.create(
                material=self,
                order_id=order_id,
                quantity=quantity
            )
            # Уменьшаем доступное количество
            self.current_quantity -= quantity
            self.save()
            return reservation
        return None
    
    def consume(self, quantity, order_id):
        """Списание материала после выполнения заказа"""
        # Находим резервирование для этого заказа
        reservation = MaterialReservation.objects.filter(
            material=self,
            order_id=order_id,
            quantity=quantity
        ).first()
        
        if reservation:
            # Удаляем резервирование (материал уже списан при резервировании)
            reservation.delete()
            return True
        return False
    
    def release(self, quantity, order_id):
        """Освобождение резервирования (отмена заказа)"""
        # Находим резервирование
        reservation = MaterialReservation.objects.filter(
            material=self,
            order_id=order_id,
            quantity=quantity
        ).first()
        
        if reservation:
            # Возвращаем материал на склад
            self.current_quantity += quantity
            self.save()
            reservation.delete()
            return True
        return False

class MaterialRecipe(models.Model):
    """Рецепт расхода материала на товар"""
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, 
                               related_name='material_recipes')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='recipes')
    consumption_rate = models.DecimalField('Норма расхода', max_digits=10, decimal_places=3)
    waste_factor = models.DecimalField('Коэффициент отходов', max_digits=5, decimal_places=2, default=0.1)
    
    class Meta:
        verbose_name = 'Рецепт материала'
        verbose_name_plural = 'Рецепты материалов'
        unique_together = ['product', 'material']
    
    def __str__(self):
        return f"{self.product.name} - {self.material.name}: {self.consumption_rate}"
    
    def get_total_consumption(self, quantity=1):
        """Общий расход с учетом отходов"""
        return self.consumption_rate * quantity * (1 + self.waste_factor)
    
    def reserve_for_order(self, order_quantity, order_id):
        """Резервирование материала для конкретного заказа"""
        total_needed = self.get_total_consumption(order_quantity)
        return self.material.reserve(total_needed, order_id)

class MaterialReservation(models.Model):
    """Фиксация резервирования материала для заказа"""
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='reservations')
    order_id = models.IntegerField('ID заказа')  # Ссылка на заказ в системе
    quantity = models.DecimalField('Количество', max_digits=12, decimal_places=3)
    reserved_at = models.DateTimeField('Время резервирования', auto_now_add=True)
    status = models.CharField('Статус', max_length=20, choices=[
        ('reserved', 'Зарезервировано'),
        ('consumed', 'Списано'),
        ('released', 'Освобождено'),
    ], default='reserved')
    
    class Meta:
        verbose_name = 'Резервирование материала'
        verbose_name_plural = 'Резервирования материалов'
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Резерв {self.material.name} для заказа #{self.order_id}"
    
    def consume(self):
        """Отметка о списании материала"""
        self.status = 'consumed'
        self.save()
    
    def release(self):
        """Освобождение резерва"""
        # Возвращаем материал на склад
        self.material.current_quantity += self.quantity
        self.material.save()
        
        self.status = 'released'
        self.save()