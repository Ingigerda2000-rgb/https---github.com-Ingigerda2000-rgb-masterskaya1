# materials/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Material, MaterialRecipe, MaterialReservation

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'master', 'current_quantity_display', 'unit_display', 
                    'min_quantity_display', 'price_per_unit_display', 'stock_value_display',
                    'status_indicator', 'is_active']
    list_filter = ['master', 'is_active', 'unit', 'created_at']
    search_fields = ['name', 'color', 'supplier', 'master__email', 'master__first_name', 'master__last_name']
    readonly_fields = ['created_at', 'updated_at', 'stock_value_display']
    list_per_page = 20
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('master', 'name', 'is_active')
        }),
        ('Количественные характеристики', {
            'fields': ('current_quantity', 'unit', 'min_quantity')
        }),
        ('Финансовые характеристики', {
            'fields': ('price_per_unit', 'stock_value_display')
        }),
        ('Технические характеристики', {
            'fields': ('color', 'texture')
        }),
        ('Информация о поставщике', {
            'fields': ('supplier', 'supplier_contact')
        }),
        ('Дополнительная информация', {
            'fields': ('notes',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def current_quantity_display(self, obj):
        return f"{obj.current_quantity}"
    current_quantity_display.short_description = 'Количество'
    
    def unit_display(self, obj):
        return obj.get_unit_display()
    unit_display.short_description = 'Ед. изм.'
    
    def min_quantity_display(self, obj):
        return f"{obj.min_quantity}"
    min_quantity_display.short_description = 'Мин. запас'
    
    def price_per_unit_display(self, obj):
        return f"{obj.price_per_unit} ₽"
    price_per_unit_display.short_description = 'Цена за ед.'
    
    def stock_value_display(self, obj):
        return f"{obj.stock_value:.2f} ₽"
    stock_value_display.short_description = 'Стоимость запаса'
    
    def status_indicator(self, obj):
        if obj.current_quantity == 0:
            color = 'red'
            text = 'Нет в наличии'
        elif obj.is_low_stock:
            color = 'orange'
            text = 'Низкий запас'
        else:
            color = 'green'
            text = 'В норме'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color, text
        )
    status_indicator.short_description = 'Статус'


@admin.register(MaterialRecipe)
class MaterialRecipeAdmin(admin.ModelAdmin):
    list_display = ['product', 'material', 'consumption_rate_display', 
                    'waste_factor_percent', 'total_consumption_display', 'auto_consume']
    list_filter = ['product__master', 'auto_consume', 'material__unit']
    search_fields = ['product__name', 'material__name']
    raw_id_fields = ['product', 'material']
    list_per_page = 20
    
    def consumption_rate_display(self, obj):
        return f"{obj.consumption_rate} {obj.material.get_unit_display()}"
    consumption_rate_display.short_description = 'Норма расхода'
    
    def waste_factor_percent(self, obj):
        return f"{obj.waste_factor * 100:.1f}%"
    waste_factor_percent.short_description = 'Отходы'
    
    def total_consumption_display(self, obj):
        total = obj.consumption_rate * (1 + obj.waste_factor)
        return f"{total:.3f} {obj.material.get_unit_display()}"
    total_consumption_display.short_description = 'Всего с отходами'


@admin.register(MaterialReservation)
class MaterialReservationAdmin(admin.ModelAdmin):
    list_display = ['material', 'order_item_link', 'quantity_display', 
                    'status_display', 'reserved_at', 'consumed_at']
    list_filter = ['status', 'reserved_at', 'material__master']
    search_fields = ['material__name', 'order_item__order__id']
    readonly_fields = ['reserved_at', 'consumed_at', 'released_at']
    list_per_page = 20
    
    def order_item_link(self, obj):
        if obj.order_item:
            url = f"/admin/orders/orderitem/{obj.order_item.id}/change/"
            return format_html('<a href="{}">Заказ #{}</a>', url, obj.order_item.order.id)
        return "Ручное списание"
    order_item_link.short_description = 'Заказ'
    
    def quantity_display(self, obj):
        return f"{obj.quantity} {obj.material.get_unit_display()}"
    quantity_display.short_description = 'Количество'
    
    def status_display(self, obj):
        colors = {
            'reserved': 'warning',
            'consumed': 'success',
            'released': 'info',
            'cancelled': 'secondary'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Статус'