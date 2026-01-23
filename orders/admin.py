from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderStatusHistory


class OrderStatusHistoryInline(admin.TabularInline):
    """История статусов в админке заказа"""
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['changed_at', 'changed_by', 'notification_sent']
    fields = ['status', 'stage_detail', 'comment', 'photo_report', 
              'changed_at', 'changed_by', 'notification_sent']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'customer_name', 'total_amount', 
                    'status_badge', 'created_at', 'tracking_number']
    list_filter = ['status', 'created_at', 'payment_method']
    search_fields = ['id', 'customer_name', 'customer_email', 
                     'customer_phone', 'tracking_number']
    readonly_fields = ['created_at', 'updated_at', 'payment_id']
    fieldsets = [
        ('Основная информация', {
            'fields': ['user', 'total_amount', 'status', 'payment_id', 'payment_method']
        }),
        ('Данные получателя', {
            'fields': ['customer_name', 'customer_email', 'customer_phone']
        }),
        ('Доставка', {
            'fields': ['delivery_address', 'postal_code', 'city', 'region', 'country',
                      'tracking_number', 'estimated_delivery_date']
        }),
        ('Системная информация', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    inlines = [OrderStatusHistoryInline]
    actions = ['mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']
    
    def status_badge(self, obj):
        colors = {
            'pending': 'secondary',
            'paid': 'info',
            'processing': 'primary',
            'in_work': 'warning',
            'preparing_for_shipment': 'warning',
            'shipped': 'success',
            'delivered': 'success',
            'cancelled': 'danger',
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'
    
    def mark_as_shipped(self, request, queryset):
        updated = 0
        for order in queryset.filter(status__in=['processing', 'in_work', 'preparing_for_shipment']):
            try:
                order.update_status('shipped', user=request.user)
                updated += 1
            except ValueError:
                pass
        self.message_user(request, f'{updated} заказов помечены как отправленные')
    mark_as_shipped.short_description = "Пометить как отправленные"
    
    def mark_as_delivered(self, request, queryset):
        updated = 0
        for order in queryset.filter(status='shipped'):
            try:
                order.update_status('delivered', user=request.user)
                updated += 1
            except ValueError:
                pass
        self.message_user(request, f'{updated} заказов помечены как доставленные')
    mark_as_delivered.short_description = "Пометить как доставленные"
    
    def mark_as_cancelled(self, request, queryset):
        updated = 0
        for order in queryset.exclude(status__in=['delivered', 'cancelled']):
            try:
                order.update_status('cancelled', user=request.user, 
                                   comment='Отменено администратором')
                updated += 1
            except ValueError:
                pass
        self.message_user(request, f'{updated} заказов отменены')
    mark_as_cancelled.short_description = "Отменить выбранные заказы"


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status_badge', 'changed_by', 'changed_at', 'notification_sent']
    list_filter = ['status', 'changed_at', 'notification_sent']
    search_fields = ['order__id', 'comment', 'stage_detail']
    readonly_fields = ['changed_at']
    
    def status_badge(self, obj):
        colors = {
            'pending': 'secondary',
            'paid': 'info',
            'processing': 'primary',
            'in_work': 'warning',
            'preparing_for_shipment': 'warning',
            'shipped': 'success',
            'delivered': 'success',
            'cancelled': 'danger',
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'