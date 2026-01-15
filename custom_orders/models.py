from django.db import models
from django.contrib.postgres.fields import JSONField
from accounts.models import User
from products.models import Product
from orders.models import OrderItem

class ProductTemplate(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='templates')
    name = models.CharField('Название шаблона', max_length=200)
    description = models.TextField('Описание шаблона', blank=True)
    configuration = models.JSONField('Конфигурация параметров', default=dict)
    base_price = models.DecimalField('Базовая цена', max_digits=10, decimal_places=2)
    base_production_days = models.IntegerField('Базовый срок изготовления (дней)', default=5)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Шаблон товара'
        verbose_name_plural = 'Шаблоны товаров'
    
    def __str__(self):
        return f"{self.name} ({self.product.name})"
    
    def calculate_price(self, selections):
        """Расчёт стоимости по выбору пользователя"""
        total_price = self.base_price
        
        # Добавляем стоимость выбранных материалов
        if 'materials' in selections:
            for material_choice in selections['materials']:
                total_price += material_choice.get('price', 0)
        
        # Добавляем стоимость параметров
        if 'parameters' in selections:
            for param_choice in selections['parameters']:
                total_price += param_choice.get('price', 0)
        
        # Добавляем стоимость персонализации
        if 'personalization' in selections:
            total_price += selections['personalization'].get('price', 0)
        
        return total_price
    
    def calculate_production_time(self, selections):
        """Расчёт срока изготовления по выбору пользователя"""
        total_days = self.base_production_days
        
        # Добавляем время на материалы
        if 'materials' in selections:
            for material_choice in selections['materials']:
                total_days += material_choice.get('additional_days', 0)
        
        # Добавляем время на параметры
        if 'parameters' in selections:
            for param_choice in selections['parameters']:
                total_days += param_choice.get('additional_days', 0)
        
        # Добавляем время на персонализацию
        if 'personalization' in selections:
            total_days += selections['personalization'].get('additional_days', 0)
        
        return total_days

class CustomOrderSpecification(models.Model):
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name='custom_specification')
    template = models.ForeignKey(ProductTemplate, on_delete=models.PROTECT, related_name='custom_orders')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_orders')
    
    # Конфигурация пользователя
    configuration = models.JSONField('Конфигурация', default=dict)
    
    # Итоговые расчёты
    total_price = models.DecimalField('Итоговая цена', max_digits=10, decimal_places=2)
    production_days = models.IntegerField('Срок изготовления (дней)')
    
    # Предварительный эскиз
    sketch = models.ImageField('Эскиз', upload_to='custom_orders/sketches/', blank=True, null=True)
    customer_notes = models.TextField('Примечания покупателя', blank=True)
    
    # Статус
    is_approved = models.BooleanField('Согласовано', default=False)
    approved_at = models.DateTimeField('Дата согласования', null=True, blank=True)
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Спецификация кастомного заказа'
        verbose_name_plural = 'Спецификации кастомных заказов'
    
    def __str__(self):
        return f"Кастомный заказ {self.order_item.order.order_number}"
    
    def get_materials_required(self):
        """Получение необходимых материалов"""
        materials = []
        for material_recipe in self.template.product.material_recipes.all():
            required_qty = material_recipe.calculate_required(1)
            materials.append({
                'material': material_recipe.material,
                'quantity': required_qty,
                'recipe': material_recipe,
            })
        return materials