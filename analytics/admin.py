from django.contrib import admin
from django.utils.html import format_html
from .models import DailyStat, MasterStat
from accounts.models import User

@admin.register(DailyStat)
class DailyStatAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_orders', 'total_revenue', 'total_items_sold', 'new_users', 'active_users')
    list_filter = ('date',)
    search_fields = ('date',)
    readonly_fields = ('created_at', 'updated_at', 'revenue_per_order')
    fieldsets = (
        ('Основные показатели', {
            'fields': ('date', 'total_orders', 'total_revenue', 'total_items_sold')
        }),
        ('Пользователи', {
            'fields': ('new_users', 'active_users')
        }),
        ('Конверсия', {
            'fields': ('cart_abandonment_rate', 'revenue_per_order')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def revenue_per_order(self, obj):
        if obj.total_orders > 0:
            return f"{obj.total_revenue / obj.total_orders:.2f} ₽"
        return "0 ₽"
    revenue_per_order.short_description = 'Средний чек'
    
    def has_add_permission(self, request):
        """Запретить добавление вручную - статистика генерируется автоматически"""
        return False

@admin.register(MasterStat)
class MasterStatAdmin(admin.ModelAdmin):
    list_display = ('master', 'period_start', 'period_end', 'orders_count', 'revenue', 'calculate_profit', 'calculate_margin')
    list_filter = ('period_start', 'period_end', 'master')
    search_fields = ('master__email', 'top_product')
    readonly_fields = ('generated_at', 'calculate_profit', 'calculate_margin')
    fieldsets = (
        ('Период и мастер', {
            'fields': ('master', 'period_start', 'period_end')
        }),
        ('Продажи', {
            'fields': ('orders_count', 'revenue', 'average_order_value')
        }),
        ('Товары', {
            'fields': ('top_product', 'top_product_sales')
        }),
        ('Материалы', {
            'fields': ('materials_cost', 'materials_used')
        }),
        ('Финансовые показатели', {
            'fields': ('calculate_profit', 'calculate_margin')
        }),
        ('Дата генерации', {
            'fields': ('generated_at',),
            'classes': ('collapse',)
        }),
    )
    
    def calculate_profit(self, obj):
        return f"{obj.calculate_profit()} ₽"
    calculate_profit.short_description = 'Прибыль'
    
    def calculate_margin(self, obj):
        return f"{obj.calculate_margin():.1f}%"
    calculate_margin.short_description = 'Маржа'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and request.user.role == 'master':
            return qs.filter(master=request.user)
        return qs