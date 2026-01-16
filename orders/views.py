from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import transaction
from cart.views import get_or_create_cart
from .models import Order, OrderItem
from .forms import OrderForm

def checkout(request):
    """Оформление заказа"""
    cart = get_or_create_cart(request)
    
    # Проверяем, есть ли товары в корзине
    if not cart.items.exists():
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('cart_view')
    
    # Проверяем доступность всех товаров
    unavailable_items = []
    for item in cart.items.all():
        if not item.is_available():
            unavailable_items.append(item)
    
    if unavailable_items:
        messages.error(request, 'Некоторые товары в корзине недоступны. Пожалуйста, проверьте корзину.')
        return redirect('cart_view')
    
    # Рассчитываем стоимость
    items_total = cart.calculate_total()
    delivery_cost = calculate_delivery_cost(request)  # Функция для расчета доставки
    total = items_total + delivery_cost
    
    if request.method == 'POST':
        # Для авторизованных пользователей используем их данные
        if request.user.is_authenticated:
            form = OrderForm(request.POST, user=request.user)
        else:
            form = OrderForm(request.POST)
            
        if form.is_valid():
            with transaction.atomic():
                # Создаем заказ
                order = form.save(commit=False)
                
                # Если пользователь авторизован, привязываем заказ к нему
                if request.user.is_authenticated:
                    order.user = request.user
                
                order.total_amount = total
                order.delivery_cost = delivery_cost
                
                # Генерируем номер заказа
                order.save()
                
                # Добавляем товары из корзины
                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price,
                        product_name=cart_item.product.name
                    )
                    
                    # Обновляем остатки товаров
                    product = cart_item.product
                    product.stock_quantity -= cart_item.quantity
                    product.save()
                
                # Очищаем корзину
                cart.clear()
                
                # Применяем промокод если есть
                promo_code = form.cleaned_data.get('promo_code')
                if promo_code:
                    success, message = order.apply_promo_code(promo_code)
                    if success:
                        messages.success(request, message)
                    else:
                        messages.warning(request, message)
                
                messages.success(request, f'Заказ #{order.order_number} успешно создан!')
                return redirect('orders:order_detail', order_id=order.id)
    else:
        form = OrderForm(user=request.user)
    
    context = {
        'form': form,
        'cart': cart,
        'items_total': items_total,
        'delivery_cost': delivery_cost,
        'total': total,
    }
    
    return render(request, 'orders/checkout.html', context)

def calculate_delivery_cost(request):
    """Расчет стоимости доставки (упрощенный)"""
    # Здесь можно интегрировать API служб доставки
    # Пока используем фиксированную стоимость или бесплатную доставку от суммы
    cart = get_or_create_cart(request)
    total = cart.calculate_total()
    
    if total >= 5000:  # Бесплатная доставка от 5000 руб
        return 0
    else:
        return 300  # Фиксированная стоимость доставки

def order_list(request):
    """Список заказов пользователя"""
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'orders/order_list.html', {'orders': orders})
    else:
        # Для неавторизованных пользователей показываем сообщение о необходимости авторизации
        messages.info(request, 'Для просмотра истории заказов необходимо авторизоваться')
        return redirect('login')

def order_detail(request, order_id):
    """Детальная страница заказа"""
    # Для авторизованных пользователей проверяем, что заказ принадлежит им
    if request.user.is_authenticated:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    else:
        # Для неавторизованных пользователей просто получаем заказ по ID
        # В реальном проекте здесь должна быть дополнительная проверка
        # например, по email или номеру телефона
        order = get_object_or_404(Order, id=order_id)
    
    return render(request, 'orders/order_detail.html', {'order': order})

# Функция apply_promo_code перенесена в приложение discounts
