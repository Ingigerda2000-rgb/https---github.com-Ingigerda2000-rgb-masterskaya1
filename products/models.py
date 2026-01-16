# products/models.py - ПРАВИЛЬНЫЙ ВАРИАНТ
from django.db import models
from django.db.models import Q
from accounts.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField('Название', max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                             related_name='children')
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Technique(models.Model):
    """Модель для техник рукоделия"""
    name = models.CharField('Название техники', max_length=100, unique=True)
    slug = models.SlugField('Slug', max_length=100, unique=True)
    description = models.TextField('Описание', blank=True)
    icon = models.CharField('Иконка', max_length=50, blank=True, 
                           help_text='Название иконки Bootstrap, например: bi-scissors')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Техника'
        verbose_name_plural = 'Техники'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активен'),
        ('inactive', 'Снят с продажи'),
        ('draft', 'Черновик'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Начинающий'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый'),
        ('expert', 'Эксперт'),
    ]
    
    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    master = models.ForeignKey(User, on_delete=models.CASCADE, 
                              limit_choices_to={'role': 'master'},
                              related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    
    # Связь с материалами
    materials = models.ManyToManyField(
        'materials.Material',
        related_name='products',
        blank=True,
        verbose_name='Материалы'
    )
    
    stock_quantity = models.IntegerField('Количество на складе', default=0)
    status = models.CharField('Статус', max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    # Поля для техники рукоделия
    technique = models.CharField('Техника изготовления', max_length=100, blank=True)
    difficulty_level = models.CharField('Уровень сложности', max_length=50, 
                                       choices=DIFFICULTY_CHOICES, blank=True)
    production_time_days = models.IntegerField('Срок изготовления (дней)', default=1)
    
    # Поля для фильтрации
    weight = models.DecimalField('Вес (г)', max_digits=8, decimal_places=2, null=True, blank=True)
    dimensions = models.CharField('Размеры', max_length=100, blank=True)
    color = models.CharField('Цвет', max_length=50, blank=True)
    
    # Поля для поиска и релевантности
    search_vector = models.TextField('Вектор поиска', blank=True)
    tags = models.TextField('Теги', blank=True, help_text='Теги через запятую для улучшения поиска')
    
    # Поля для двухуровневого учета
    can_be_customized = models.BooleanField('Можно кастомизировать', default=False)
    base_cost = models.DecimalField('Базовая стоимость материалов', max_digits=10, 
                                   decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['price']),
            models.Index(fields=['created_at']),
            models.Index(fields=['technique']),
            models.Index(fields=['difficulty_level']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Автоматическое обновление поискового вектора"""
        # ВАЖНО: сначала вызываем родительский save, чтобы получить id
        super().save(*args, **kwargs)
        
        # Теперь можно обновить теги
        if not self.tags or self.tags.strip() == '':
            self._update_tags()
            # Сохраняем только поле tags
            super().save(update_fields=['tags'])
    
    def _update_tags(self):
        """Обновление тегов для товара"""
        tags_parts = [self.name]
        if self.technique:
            tags_parts.append(self.technique)
        if self.category:
            tags_parts.append(self.category.name)
        if self.color:
            tags_parts.append(self.color)
        
        # Только если товар уже сохранен
        if self.pk:
            for material in self.materials.all():
                tags_parts.append(material.name)
        
        self.tags = ', '.join(tags_parts)
    
    def is_available(self):
        """Проверка доступности товара"""
        return self.status == 'active' and self.stock_quantity > 0
    
    def get_main_image(self):
        """Получение основного изображения"""
        try:
            from .models import ProductImage
            main_image = ProductImage.objects.filter(product=self, is_main=True).first()
            if main_image:
                return main_image.image
            # Если нет основного изображения, вернуть первое изображение
            first_image = ProductImage.objects.filter(product=self).first()
            if first_image:
                return first_image.image
        except:
            pass
        return None
    
    def get_related_products(self, limit=4):
        """Получение похожих товаров"""
        return Product.objects.filter(
            Q(category=self.category) | 
            Q(materials__in=self.materials.all()) |
            Q(technique=self.technique)
        ).exclude(id=self.id).filter(status='active').distinct()[:limit]
    
    def calculate_material_cost(self, quantity=1):
        """Расчет стоимости материалов для товара"""
        try:
            from materials.models import MaterialRecipe
            
            total_cost = 0
            recipes = MaterialRecipe.objects.filter(product=self)
            
            for recipe in recipes:
                material_cost = recipe.material.price_per_unit * recipe.get_total_consumption(quantity)
                total_cost += material_cost
            
            return total_cost
        except:
            return 0
    
    def check_material_availability(self, quantity=1):
        """Проверка доступности материалов для производства"""
        try:
            from materials.models import MaterialRecipe
            
            unavailable_materials = []
            recipes = MaterialRecipe.objects.filter(product=self)
            
            for recipe in recipes:
                needed = recipe.get_total_consumption(quantity)
                if not recipe.material.check_availability(needed):
                    unavailable_materials.append({
                        'material': recipe.material,
                        'needed': needed,
                        'available': recipe.material.current_quantity
                    })
            
            return unavailable_materials
        except:
            return []
    
    def reserve_materials_for_order(self, quantity, order_id):
        """Резервирование материалов для заказа"""
        try:
            from materials.models import MaterialRecipe
            
            reservations = []
            recipes = MaterialRecipe.objects.filter(product=self)
            
            for recipe in recipes:
                needed = recipe.get_total_consumption(quantity)
                reservation = recipe.material.reserve(needed, order_id)
                if reservation:
                    reservations.append(reservation)
            
            return reservations
        except:
            return []
    
    def release_materials_for_order(self, quantity, order_id):
        """Освобождение резервирования материалов (при отмене заказа)"""
        try:
            from materials.models import MaterialRecipe
            
            released_count = 0
            recipes = MaterialRecipe.objects.filter(product=self)
            
            for recipe in recipes:
                needed = recipe.get_total_consumption(quantity)
                if recipe.material.release(needed, order_id):
                    released_count += 1
            
            return released_count
        except:
            return 0

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField('Изображение', upload_to='products/')
    is_main = models.BooleanField('Основное изображение', default=False)
    order = models.IntegerField('Порядок', default=0)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
        ordering = ['order']
    
    def __str__(self):
        return f"Изображение {self.product.name}"

class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    name = models.CharField('Название атрибута', max_length=100)
    value = models.CharField('Значение', max_length=255)
    
    class Meta:
        verbose_name = 'Атрибут товара'
        verbose_name_plural = 'Атрибуты товаров'
    
    def __str__(self):
        return f"{self.name}: {self.value}"

class Favorite(models.Model):
    """Модель для избранных товаров пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField('Дата добавления', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ['user', 'product']  # Пользователь может добавить товар в избранное только один раз
    
    def __str__(self):
        return f"{self.user.email} - {self.product.name}"
