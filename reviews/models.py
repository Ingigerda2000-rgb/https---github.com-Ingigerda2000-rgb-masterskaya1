from django.db import models
from accounts.models import User
from products.models import Product
from orders.models import Order

class Review(models.Model):
    RATING_CHOICES = [
        (1, '★☆☆☆☆'),
        (2, '★★☆☆☆'),
        (3, '★★★☆☆'),
        (4, '★★★★☆'),
        (5, '★★★★★'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, 
                             related_name='reviews', help_text='Заказ, по которому оставлен отзыв')
    
    rating = models.IntegerField('Оценка', choices=RATING_CHOICES)
    title = models.CharField('Заголовок', max_length=200, blank=True)
    text = models.TextField('Текст отзыва')
    
    # Проверка факта покупки
    purchase_verified = models.BooleanField('Покупка подтверждена', default=False)
    
    # Модерация
    is_approved = models.BooleanField('Одобрен', default=False)
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                    blank=True, related_name='moderated_reviews')
    moderation_notes = models.TextField('Заметки модератора', blank=True)
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # Один отзыв на товар от пользователя
    
    def __str__(self):
        return f"Отзыв на {self.product.name} от {self.user.email}"
    
    def verify_purchase(self):
        """Проверка факта покупки товара"""
        if self.order:
            # Проверяем, что товар есть в заказе
            order_items = self.order.items.filter(product=self.product)
            self.purchase_verified = order_items.exists()
            self.save()
            return self.purchase_verified
        return False

class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField('Изображение', upload_to='reviews/')
    uploaded_at = models.DateTimeField('Дата загрузки', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Изображение отзыва'
        verbose_name_plural = 'Изображения отзывов'
    
    def __str__(self):
        return f"Изображение к отзыву #{self.review.id}"