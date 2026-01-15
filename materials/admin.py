# materials/admin.py
from django.contrib import admin
from .models import Material, MaterialRecipe, MaterialReservation

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'master', 'current_quantity', 'unit', 'min_quantity', 
                   'price_per_unit', 'is_low_stock', 'created_at')
    list_filter = ('master', 'unit', 'created_at')
    search_fields = ('name', 'color', 'texture', 'supplier')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'master', 'unit', 'color', 'texture')
        }),
        ('Количественные показатели', {
            'fields': ('current_quantity', 'min_quantity', 'price_per_unit')
        }),
        ('Дополнительно', {
            'fields': ('supplier', 'created_at', 'updated_at')
        }),
    )
    
    def is_low_stock(self, obj):
        return obj.is_low_stock()
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Низкий запас'

@admin.register(MaterialRecipe)
class MaterialRecipeAdmin(admin.ModelAdmin):
    list_display = ('product', 'material', 'consumption_rate', 'waste_factor', 
                   'get_total_consumption_display')
    list_filter = ('material',)
    search_fields = ('product__name', 'material__name')
    
    def get_total_consumption_display(self, obj):
        return f"{obj.get_total_consumption():.3f}"
    get_total_consumption_display.short_description = 'Расход с отходами'

@admin.register(MaterialReservation)
class MaterialReservationAdmin(admin.ModelAdmin):
    list_display = ('material', 'order_id', 'quantity', 'status', 'reserved_at')
    list_filter = ('status', 'reserved_at', 'material')
    search_fields = ('material__name', 'order_id')
    readonly_fields = ('reserved_at',)
    list_editable = ('status',)
    
    actions = ['consume_reservations', 'release_reservations']
    
    def consume_reservations(self, request, queryset):
        """Действие: списать резервирования"""
        for reservation in queryset.filter(status='reserved'):
            reservation.consume()
        self.message_user(request, f"Списано {queryset.count()} резервирований.")
    consume_reservations.short_description = "Списать выбранные резервирования"
    
    def release_reservations(self, request, queryset):
        """Действие: освободить резервирования"""
        for reservation in queryset.filter(status='reserved'):
            reservation.release()
        self.message_user(request, f"Освобождено {queryset.count()} резервирований.")
    release_reservations.short_description = "Освободить выбранные резервирования"