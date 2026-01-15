from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ('product', 'quantity', 'calculate_subtotal')
    readonly_fields = ('calculate_subtotal',)
    
    def calculate_subtotal(self, obj):
        return f"{obj.calculate_subtotal()} ₽"
    calculate_subtotal.short_description = 'Сумма'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_count', 'calculate_total', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'session_key')
    readonly_fields = ('created_at', 'updated_at', 'calculate_total', 'item_count')
    inlines = [CartItemInline]
    fields = ('user', 'session_key', 'item_count', 'calculate_total', 'created_at', 'updated_at')
    
    def calculate_total(self, obj):
        return f"{obj.calculate_total()} ₽"
    calculate_total.short_description = 'Общая сумма'
    
    def item_count(self, obj):
        return obj.item_count()
    item_count.short_description = 'Количество позиций'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'calculate_subtotal', 'added_at')
    list_filter = ('added_at', 'cart__user')
    search_fields = ('product__name', 'cart__user__email')
    readonly_fields = ('added_at', 'calculate_subtotal')
    
    def calculate_subtotal(self, obj):
        return f"{obj.calculate_subtotal()} ₽"
    calculate_subtotal.short_description = 'Сумма'