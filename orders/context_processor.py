from .models import ORDER_STATUS_CHOICES

def order_statuses(request):
    """Добавляет статусы заказов в контекст всех шаблонов"""
    return {
        'ORDER_STATUS_CHOICES': ORDER_STATUS_CHOICES,
        'status_colors': {
            'pending': 'secondary',
            'paid': 'info',
            'processing': 'primary',
            'in_work': 'warning',
            'preparing_for_shipment': 'warning',
            'shipped': 'success',
            'delivered': 'success',
            'cancelled': 'danger',
        }
    }