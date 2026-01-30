# orders/templatetags/order_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Получить элемент из словаря по ключу в шаблоне"""
    return dictionary.get(key)

@register.filter
def status_color(status):
    """Получить цвет для статуса"""
    colors = {
        'pending': 'secondary',
        'confirmed': 'info',
        'in_progress': 'primary',
        'ready_for_shipping': 'warning',
        'shipped': 'info',
        'delivered': 'success',
        'cancelled': 'danger',
        'refunded': 'dark',
    }
    return colors.get(status, 'secondary')

@register.filter
def status_icon(status):
    """Получить иконку для статуса"""
    icons = {
        'pending': 'bi-hourglass-split',
        'confirmed': 'bi-check-circle',
        'in_progress': 'bi-tools',
        'ready_for_shipping': 'bi-box-seam',
        'shipped': 'bi-truck',
        'delivered': 'bi-house-check',
        'cancelled': 'bi-x-circle',
        'refunded': 'bi-arrow-counterclockwise',
    }
    return icons.get(status, 'bi-question-circle')