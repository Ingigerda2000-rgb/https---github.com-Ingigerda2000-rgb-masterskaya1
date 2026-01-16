from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import PromoCode
from cart.views import get_or_create_cart

@require_POST
def apply_promo_code(request):
    """Применение промокода (AJAX)"""
    promo_code = request.POST.get('promo_code')
    cart = get_or_create_cart(request)
    items_total = cart.calculate_total()
    
    try:
        promo = PromoCode.objects.get(code=promo_code, is_active=True)
        
        if promo.is_valid(items_total):
            discount = promo.calculate_discount(items_total)
            return JsonResponse({
                'success': True,
                'discount': float(discount),
                'new_total': float(items_total - discount),
                'message': f'Промокод применён! Скидка: {discount}₽'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Промокод недействителен для данной суммы заказа'
            })
    
    except PromoCode.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Промокод не найден'
        })
