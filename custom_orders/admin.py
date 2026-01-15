from django.contrib import admin
from django.utils.html import format_html
from django.db.models import JSONField
from django.forms import Textarea
from .models import ProductTemplate, CustomOrderSpecification
from accounts.models import User
from django.utils import timezone
import json

@admin.register(ProductTemplate)
class ProductTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'base_price', 'base_production_days', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'product__category')
    search_fields = ('name', 'description', 'product__name')
    list_editable = ('is_active', 'base_price')
    readonly_fields = ('created_at', 'preview_configuration')
    fieldsets = (
        ('Основная информация', {
            'fields': ('product', 'name', 'description', 'is_active')
        }),
        ('Базовые значения', {
            'fields': ('base_price', 'base_production_days')
        }),
        ('Конфигурация конструктора (JSON)', {
            'fields': ('configuration', 'preview_configuration'),
            'classes': ('wide',)
        }),
        ('Дата создания', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['configuration'].widget = Textarea(attrs={
            'rows': 20,
            'cols': 80,
            'style': 'font-family: monospace;'
        })
        return form
    
    def preview_configuration(self, obj):
        if obj.configuration:
            html = '<div style="max-height: 200px; overflow-y: auto; padding: 10px; background: #f5f5f5; border: 1px solid #ddd; font-family: monospace;">'
            html += '<pre style="margin: 0;">{}</pre>'.format(json.dumps(obj.configuration, indent=2, ensure_ascii=False))
            html += '</div>'
            return format_html(html)
        return "Конфигурация не задана"
    preview_configuration.short_description = 'Предпросмотр конфигурации'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and request.user.role == 'master':
            return qs.filter(product__master=request.user)
        return qs

@admin.register(CustomOrderSpecification)
class CustomOrderSpecificationAdmin(admin.ModelAdmin):
    list_display = ('order_item', 'template', 'user', 'total_price', 'production_days', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at', 'template__product__category')
    search_fields = ('order_item__order__order_number', 'user__email', 'template__name')
    readonly_fields = ('created_at', 'approved_at', 'preview_configuration', 'sketch_preview')
    fieldsets = (
        ('Основная информация', {
            'fields': ('order_item', 'template', 'user', 'total_price', 'production_days')
        }),
        ('Конфигурация заказа', {
            'fields': ('configuration', 'preview_configuration', 'customer_notes'),
            'classes': ('wide',)
        }),
        ('Визуализация', {
            'fields': ('sketch', 'sketch_preview'),
            'classes': ('collapse',)
        }),
        ('Согласование', {
            'fields': ('is_approved', 'approved_at')
        }),
        ('Дата создания', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['configuration'].widget = Textarea(attrs={
            'rows': 20,
            'cols': 80,
            'style': 'font-family: monospace;'
        })
        return form
    
    def sketch_preview(self, obj):
        if obj.sketch:
            return format_html('<img src="{}" height="150" />', obj.sketch.url)
        return "Эскиз не загружен"
    sketch_preview.short_description = 'Превью эскиза'
    
    def preview_configuration(self, obj):
        if obj.configuration:
            html = '<div style="max-height: 200px; overflow-y: auto; padding: 10px; background: #f5f5f5; border: 1px solid #ddd; font-family: monospace;">'
            html += '<pre style="margin: 0;">{}</pre>'.format(json.dumps(obj.configuration, indent=2, ensure_ascii=False))
            html += '</div>'
            return format_html(html)
        return "Конфигурация не задана"
    preview_configuration.short_description = 'Предпросмотр конфигурации'
    
    def save_model(self, request, obj, form, change):
        if change and 'is_approved' in form.changed_data and obj.is_approved:
            obj.approved_at = timezone.now()
        super().save_model(request, obj, form, change)