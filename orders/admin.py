from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, OrderStatusHistory
from accounts.models import User

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'product_name', 'quantity', 'price', 'calculate_subtotal')
    readonly_fields = ('product_name', 'calculate_subtotal')
    
    def calculate_subtotal(self, obj):
        return f"{obj.calculate_subtotal()} ₽"
    calculate_subtotal.short_description = 'Сумма'

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    fields = ('status', 'stage_detail', 'comment', 'changed_by', 'changed_at', 'notify_customer')
    readonly_fields = ('changed_at', 'changed_by')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "changed_by":
            kwargs["initial"] = request.user
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_amount', 'created_at', 'customer_phone')
    list_filter = ('status', 'created_at', 'payment_method')
    search_fields = ('order_number', 'user__email', 'customer_name', 'customer_phone', 'tracking_number')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'paid_at', 'calculate_total')
    list_editable = ('status',)
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('order_number', 'user', 'status', 'total_amount')
        }),
        ('Данные покупателя', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Доставка', {
            'fields': ('delivery_address', 'delivery_cost', 'delivery_method', 'tracking_number')
        }),
        ('Оплата', {
            'fields': ('payment_method', 'payment_id', 'paid_at', 'discount_amount', 'promo_code')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def calculate_total(self, obj):
        return f"{obj.calculate_total()} ₽"
    calculate_total.short_description = 'Пересчитанная сумма'
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            # Автоматически создаём запись в истории статусов
            OrderStatusHistory.objects.create(
                order=obj,
                status=obj.status,
                changed_by=request.user,
                comment=f'Статус изменён в админке на "{obj.get_status_display()}"'
            )
        super().save_model(request, obj, form, change)

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'changed_by', 'changed_at', 'notify_customer')
    list_filter = ('status', 'changed_at', 'notify_customer')
    search_fields = ('order__order_number', 'stage_detail', 'comment')
    readonly_fields = ('changed_at',)
    fields = ('order', 'status', 'stage_detail', 'comment', 'photo', 'changed_by', 'notify_customer')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "changed_by":
            kwargs["initial"] = request.user
        return super().formfield_for_foreignkey(db_field, request, **kwargs)