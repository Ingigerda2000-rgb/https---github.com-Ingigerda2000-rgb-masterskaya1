from django.contrib import admin
from django.utils.html import format_html
from .models import Review, ReviewImage
from accounts.models import User

class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 0
    fields = ('image', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="50" />', obj.image.url)
        return "Нет изображения"
    image_preview.short_description = 'Превью'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating_stars', 'title', 'purchase_verified', 'is_approved', 'created_at')
    list_filter = ('rating', 'purchase_verified', 'is_approved', 'created_at', 'product__category')
    search_fields = ('product__name', 'user__email', 'title', 'text')
    list_editable = ('is_approved', 'purchase_verified')
    readonly_fields = ('created_at', 'updated_at', 'rating_stars', 'verified_purchase_button')
    fieldsets = (
        ('Основная информация', {
            'fields': ('product', 'user', 'order', 'rating', 'rating_stars')
        }),
        ('Содержание отзыва', {
            'fields': ('title', 'text')
        }),
        ('Проверка и модерация', {
            'fields': ('purchase_verified', 'verified_purchase_button', 'is_approved', 'moderated_by', 'moderation_notes')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ReviewImageInline]
    
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        color = {
            1: 'red',
            2: 'orange',
            3: 'gold',
            4: 'lightgreen',
            5: 'green'
        }.get(obj.rating, 'black')
        return format_html('<span style="color: {}; font-size: 16px;">{}</span>', color, stars)
    rating_stars.short_description = 'Рейтинг'
    
    def verified_purchase_button(self, obj):
        if obj.purchase_verified:
            return format_html('<span style="color: green; font-weight: bold;">✓ Подтверждено</span>')
        else:
            return format_html(
                '<a href="{}" class="button">Подтвердить покупку</a>',
                f'/admin/reviews/review/{obj.id}/verify_purchase/'
            )
    verified_purchase_button.short_description = 'Подтверждение покупки'
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/verify_purchase/', self.verify_purchase, name='verify_purchase'),
        ]
        return custom_urls + urls
    
    def verify_purchase(self, request, object_id):
        from django.shortcuts import redirect
        review = self.get_object(request, object_id)
        review.verify_purchase()
        self.message_user(request, f'Покупка для отзыва #{review.id} подтверждена')
        return redirect('..')