from django import template

register = template.Library()

@register.filter
def status_color(status):
    """Возвращает цвет CSS класса для статуса"""
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
    return colors.get(status, 'secondary')

@register.filter
def status_display(status):
    """Возвращает отображаемое имя статуса"""
    from orders.models import ORDER_STATUS_CHOICES
    status_dict = dict(ORDER_STATUS_CHOICES)
    return status_dict.get(status, status)

@register.filter
def get_item(dictionary, key):
    """Возвращает значение из словаря по ключу"""
    return dictionary.get(key)

@register.filter
def to_dict(choices):
    """Преобразует choices в словарь"""
    return dict(choices)

@register.filter
def multiply(value, arg):
    """Умножает значение на аргумент"""
    return value * arg

@register.filter
def divide(value, arg):
    """Делит значение на аргумент"""
    try:
        return value / arg
    except ZeroDivisionError:
        return 0