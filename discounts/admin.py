from django.contrib import admin
from .models import PromoCode, Discount

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'is_active', 'used_count', 'valid_from', 'valid_to')
    list_filter = ('is_active', 'discount_type')
    search_fields = ('code',)
    date_hierarchy = 'created_at'

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('order', 'discount_amount', 'promo_code')
    list_filter = ('promo_code',)
    search_fields = ('order__order_number', 'discount_reason')
