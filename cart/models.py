from django.db import models
from accounts.models import User
from products.models import Product

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts', null=True, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    session_key = models.CharField('Ключ сессии', max_length=40, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
    
    def __str__(self):
        if self.user:
            return f"Корзина пользователя {self.user.email}"
        else:
            return f"Корзина анонимного пользователя (сессия: {self.session_key})"
    
    def calculate_total(self):
        """Расчет общей суммы корзины"""
        total = sum(item.calculate_subtotal() for item in self.items.all())
        return total
    
    def item_count(self):
        """Количество позиций в корзине"""
        return self.items.count()
    
    def clear(self):
        """Очистка корзины"""
        self.items.all().delete()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.IntegerField('Количество', default=1)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2, null=True, blank=True)
    added_at = models.DateTimeField('Дата добавления', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Элементы корзины'
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
    
    def calculate_subtotal(self):
        """Расчет стоимости позиции"""
        price = self.price if self.price is not None else self.product.price
        return price * self.quantity
    
    def is_available(self):
        """Проверка доступности изделия"""
        return self.product.is_available() and self.product.stock_quantity >= self.quantity