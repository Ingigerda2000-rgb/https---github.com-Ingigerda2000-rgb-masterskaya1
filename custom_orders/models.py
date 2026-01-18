from django.db import models
from django.utils import timezone  # Добавили импорт timezone
from accounts.models import User
from products.models import Product, Technique
from orders.models import OrderItem
import json

class ProductTemplate(models.Model):
    """Шаблон для кастомизации товара"""
    PRODUCT_TYPES = [
        ('clothing', 'Одежда'),
        ('accessory', 'Аксессуар'),
        ('decor', 'Декор'),
        ('jewelry', 'Украшение'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='templates')
    name = models.CharField('Название шаблона', max_length=200)
    description = models.TextField('Описание шаблона', blank=True)
    product_type = models.CharField('Тип изделия', max_length=50, choices=PRODUCT_TYPES, default='clothing')
    
    # JSON-конфигурация параметров конструктора
    configuration = models.JSONField('Конфигурация параметров', default=dict)
    
    # Базовая стоимость и срок
    base_price = models.DecimalField('Базовая цена', max_digits=10, decimal_places=2)
    base_production_days = models.IntegerField('Базовый срок изготовления (дней)', default=5)
    
    # Минимальные и максимальные значения
    min_price = models.DecimalField('Минимальная цена', max_digits=10, decimal_places=2, default=0)
    max_price = models.DecimalField('Максимальная цена', max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Статус
    is_active = models.BooleanField('Активен', default=True)
    is_featured = models.BooleanField('Рекомендуемый', default=False)
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Шаблон товара'
        verbose_name_plural = 'Шаблоны товаров'
        ordering = ['-is_featured', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.product.name})"
    
    def get_default_configuration(self):
        """Получение конфигурации по умолчанию"""
        return {
            'sections': [
                {
                    'id': 'materials',
                    'name': 'Материалы',
                    'type': 'multiple_choice',
                    'required': True,
                    'max_selections': 3,
                    'options': []
                },
                {
                    'id': 'size',
                    'name': 'Размер',
                    'type': 'dropdown',
                    'required': True,
                    'options': []
                },
                {
                    'id': 'color',
                    'name': 'Цвет',
                    'type': 'color_picker',
                    'required': False,
                    'options': []
                },
                {
                    'id': 'personalization',
                    'name': 'Персонализация',
                    'type': 'text_input',
                    'required': False,
                    'placeholder': 'Введите текст для персонализации'
                }
            ]
        }
    
    def save(self, *args, **kwargs):
        """Сохранение с конфигурацией по умолчанию"""
        if not self.configuration:
            self.configuration = self.get_default_configuration()
        super().save(*args, **kwargs)
    
    def calculate_price(self, selections):
        """
        Расчёт стоимости по выбору пользователя
        C_total = C_base + Σ(C_material) + Σ(C_parameter) + C_personalization
        """
        total_price = float(self.base_price)
        
        # Добавляем стоимость выбранных материалов
        if 'materials' in selections:
            for material_choice in selections['materials']:
                if 'price' in material_choice:
                    total_price += float(material_choice['price'])
        
        # Добавляем стоимость параметров
        if 'parameters' in selections:
            for param_choice in selections['parameters'].values():
                if isinstance(param_choice, dict) and 'price' in param_choice:
                    total_price += float(param_choice['price'])
        
        # Добавляем стоимость персонализации
        if 'personalization' in selections and selections['personalization'].get('price'):
            total_price += float(selections['personalization']['price'])
        
        # Проверяем границы
        if self.min_price and total_price < float(self.min_price):
            total_price = float(self.min_price)
        
        if self.max_price and total_price > float(self.max_price):
            total_price = float(self.max_price)
        
        return round(total_price, 2)
    
    def calculate_production_time(self, selections):
        """
        Расчёт срока изготовления по выбору пользователя
        T_total = T_base + Σ(T_material) + Σ(T_parameter) + T_personalization
        """
        total_days = self.base_production_days
        
        # Добавляем время на материалы
        if 'materials' in selections:
            for material_choice in selections['materials']:
                if 'additional_days' in material_choice:
                    total_days += int(material_choice['additional_days'])
        
        # Добавляем время на параметры
        if 'parameters' in selections:
            for param_choice in selections['parameters'].values():
                if isinstance(param_choice, dict) and 'additional_days' in param_choice:
                    total_days += int(param_choice['additional_days'])
        
        # Добавляем время на персонализацию
        if 'personalization' in selections and selections['personalization'].get('additional_days'):
            total_days += int(selections['personalization']['additional_days'])
        
        return max(total_days, 1)  # Минимум 1 день
    
    def validate_selections(self, selections):
        """Валидация выбора пользователя"""
        errors = []
        
        # Проверяем обязательные поля
        for section in self.configuration.get('sections', []):
            if section.get('required') and section['id'] not in selections:
                errors.append(f"Поле '{section['name']}' обязательно для заполнения")
            
            # Проверяем ограничения по количеству выборов
            if section['type'] == 'multiple_choice' and 'max_selections' in section:
                selected = selections.get(section['id'], [])
                if len(selected) > section['max_selections']:
                    errors.append(f"Можно выбрать не более {section['max_selections']} вариантов в '{section['name']}'")
        
        return errors
    
    def get_available_options(self, section_id):
        """Получение доступных опций для секции"""
        for section in self.configuration.get('sections', []):
            if section['id'] == section_id:
                return section.get('options', [])
        return []
    
    def get_material_options(self):
        """Получение опций материалов для шаблона"""
        from materials.models import Material
        
        # Получаем материалы, связанные с базовым товаром
        materials = self.product.materials.all()
        
        options = []
        for material in materials:
            options.append({
                'id': str(material.id),
                'name': material.name,
                'price': float(material.price_per_unit * 2),  # Примерная стоимость материала для изделия
                'additional_days': 1,
                'description': f"{material.color} {material.texture}",
                'unit': material.get_unit_display(),
            })
        
        return options
    
    def get_size_options(self):
        """Получение опций размеров"""
        # В реальной системе это могло бы зависеть от типа изделия
        sizes = {
            'clothing': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
            'accessory': ['Один размер'],
            'decor': ['Маленький', 'Средний', 'Большой'],
            'jewelry': ['Один размер'],
        }
        
        size_options = sizes.get(self.product_type, ['Один размер'])
        
        options = []
        for i, size in enumerate(size_options):
            options.append({
                'id': str(i),
                'name': size,
                'price': 100 * i,  # Чем больше размер, тем дороже
                'additional_days': i,  # Чем больше размер, тем дольше изготовление
            })
        
        return options
    
    def update_configuration_with_dynamic_options(self):
        """Обновление конфигурации с динамическими опциями"""
        config = self.configuration.copy()
        
        for section in config.get('sections', []):
            if section['id'] == 'materials':
                section['options'] = self.get_material_options()
            elif section['id'] == 'size':
                section['options'] = self.get_size_options()
            elif section['id'] == 'color':
                section['options'] = [
                    {'id': '1', 'name': 'Красный', 'hex': '#FF0000'},
                    {'id': '2', 'name': 'Синий', 'hex': '#0000FF'},
                    {'id': '3', 'name': 'Зеленый', 'hex': '#00FF00'},
                    {'id': '4', 'name': 'Черный', 'hex': '#000000'},
                    {'id': '5', 'name': 'Белый', 'hex': '#FFFFFF'},
                ]
        
        self.configuration = config
        self.save(update_fields=['configuration'])

class CustomOrderSpecification(models.Model):
    """Спецификация кастомного заказа"""
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, 
                                      related_name='custom_specification')
    template = models.ForeignKey(ProductTemplate, on_delete=models.PROTECT, 
                                related_name='custom_orders')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_orders')
    
    # Конфигурация пользователя
    configuration = models.JSONField('Конфигурация', default=dict)
    
    # Итоговые расчёты
    total_price = models.DecimalField('Итоговая цена', max_digits=10, decimal_places=2)
    production_days = models.IntegerField('Срок изготовления (дней)')
    
    # Предварительный эскиз
    sketch = models.ImageField('Эскиз', upload_to='custom_orders/sketches/', blank=True, null=True)
    customer_notes = models.TextField('Примечания покупателя', blank=True)
    
    # Статус согласования
    is_approved = models.BooleanField('Согласовано', default=False)
    approved_at = models.DateTimeField('Дата согласования', null=True, blank=True)
    approval_notes = models.TextField('Примечания мастера', blank=True)
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Спецификация кастомного заказа'
        verbose_name_plural = 'Спецификации кастомных заказов'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Кастомный заказ {self.order_item.order.order_number}"
    
    def save(self, *args, **kwargs):
        """Автоматический расчёт при сохранении"""
        if not self.total_price and 'selections' in self.configuration:
            self.total_price = self.template.calculate_price(self.configuration['selections'])
        
        if not self.production_days and 'selections' in self.configuration:
            self.production_days = self.template.calculate_production_time(self.configuration['selections'])
        
        super().save(*args, **kwargs)
    
    def get_materials_required(self):
        """Получение необходимых материалов"""
        from materials.models import MaterialRecipe
        
        materials = []
        selections = self.configuration.get('selections', {})
        
        if 'materials' in selections:
            for material_choice in selections['materials']:
                try:
                    material_id = material_choice.get('id')
                    if material_id:
                        from materials.models import Material
                        material = Material.objects.get(id=material_id)
                        materials.append({
                            'material': material,
                            'quantity': 2,  # Примерное количество
                            'unit': material.unit,
                        })
                except Material.DoesNotExist:
                    continue
        
        return materials
    
    def get_configuration_summary(self):
        """Получение сводки конфигурации"""
        selections = self.configuration.get('selections', {})
        summary = []
        
        # Материалы
        if 'materials' in selections:
            materials = [m.get('name', 'Неизвестно') for m in selections['materials']]
            summary.append(f"Материалы: {', '.join(materials)}")
        
        # Размер
        if 'size' in selections:
            size = selections['size']
            if isinstance(size, dict):
                summary.append(f"Размер: {size.get('name', 'Неизвестно')}")
            else:
                summary.append(f"Размер: {size}")
        
        # Цвет
        if 'color' in selections:
            color = selections['color']
            if isinstance(color, dict):
                summary.append(f"Цвет: {color.get('name', 'Неизвестно')}")
            else:
                summary.append(f"Цвет: {color}")
        
        # Персонализация
        if 'personalization' in selections:
            personalization = selections['personalization']
            if isinstance(personalization, dict):
                text = personalization.get('text', '')
                if text:
                    summary.append(f"Персонализация: {text}")
        
        return summary
    
    def approve(self, notes=''):
        """Согласование заказа мастером"""
        self.is_approved = True
        self.approved_at = timezone.now()  # Теперь timezone определен
        self.approval_notes = notes
        self.save()
        
        # Обновляем статус заказа
        self.order_item.order.update_status('processing', 
                                           comment='Кастомный заказ согласован мастером')
    
    def reject(self, notes=''):
        """Отклонение заказа мастером"""
        self.is_approved = False
        self.approval_notes = notes
        self.save()
        
        # Обновляем статус заказа
        self.order_item.order.update_status('cancelled', 
                                           comment=f'Кастомный заказ отклонён: {notes}')

class DesignElement(models.Model):
    """Элемент дизайна для конструктора"""
    ELEMENT_TYPES = [
        ('pattern', 'Узор'),
        ('embroidery', 'Вышивка'),
        ('print', 'Принт'),
        ('text', 'Текст'),
        ('image', 'Изображение'),
    ]
    
    name = models.CharField('Название элемента', max_length=100)
    element_type = models.CharField('Тип элемента', max_length=20, choices=ELEMENT_TYPES)
    description = models.TextField('Описание', blank=True)
    preview_image = models.ImageField('Превью', upload_to='design_elements/', blank=True)
    svg_path = models.TextField('SVG путь', blank=True)  # Для векторных элементов
    price_addition = models.DecimalField('Наценка', max_digits=10, decimal_places=2, default=0)
    time_addition = models.IntegerField('Дополнительное время (часов)', default=0)
    is_active = models.BooleanField('Активен', default=True)
    
    class Meta:
        verbose_name = 'Элемент дизайна'
        verbose_name_plural = 'Элементы дизайна'
    
    def __str__(self):
        return self.name

class TemplateDesignElement(models.Model):
    """Связь шаблона с элементами дизайна"""
    template = models.ForeignKey(ProductTemplate, on_delete=models.CASCADE, related_name='design_elements')
    design_element = models.ForeignKey(DesignElement, on_delete=models.CASCADE, related_name='templates')
    position_x = models.IntegerField('Позиция X', default=0)
    position_y = models.IntegerField('Позиция Y', default=0)
    scale = models.DecimalField('Масштаб', max_digits=5, decimal_places=2, default=1.0)
    rotation = models.IntegerField('Поворот (градусы)', default=0)
    is_required = models.BooleanField('Обязательный', default=False)
    
    class Meta:
        verbose_name = 'Элемент дизайна шаблона'
        verbose_name_plural = 'Элементы дизайна шаблонов'
        unique_together = ['template', 'design_element']
    
    def __str__(self):
        return f"{self.design_element.name} в {self.template.name}"