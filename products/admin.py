from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Category, ProductImage, ProductAttribute

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'master', 'status', 'stock_quantity')
    list_filter = ('status', 'category', 'technique')
    search_fields = ('name', 'description', 'master__email')
    inlines = [ProductImageInline, ProductAttributeInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'price', 'category', 'master')
        }),
        ('Наличие и статус', {
            'fields': ('stock_quantity', 'status')
        }),
        ('Технические характеристики', {
            'fields': ('technique', 'difficulty_level', 'production_time_days')
        }),
        ('Физические параметры', {
            'fields': ('weight', 'dimensions', 'color')
        }),
        ('Материалы и кастомизация', {
            'fields': ('materials', 'can_be_customized', 'base_cost')
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    list_filter = ('parent',)
    search_fields = ('name', 'description')

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_main', 'order')
    list_filter = ('is_main', 'product__category')

@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'value')
    list_filter = ('name',)
    search_fields = ('product__name', 'name', 'value')