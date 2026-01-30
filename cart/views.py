# cart/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
from .models import Cart, CartItem
from products.models import Product

def get_or_create_cart(request):
    """Получение или создание корзины для пользователя"""
    if request.user.is_authenticated:
        # Для авторизованных пользователей
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # Для анонимных пользователей используем сессию
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        # Пытаемся найти корзину по session_key
        cart = Cart.objects.filter(session_key=session_key, user=None).first()
        if not cart:
            cart = Cart.objects.create(session_key=session_key, user=None)
    
    return cart

def cart_view(request):
    """Просмотр корзины"""
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product').all()
    total = cart.calculate_total()
    
    # Проверяем доступность каждого изделия
    unavailable_items = []
    for item in items:
        if not item.is_available():
            unavailable_items.append(item)
    
    context = {
        'cart': cart,
        'items': items,
        'total': total,
        'unavailable_items': unavailable_items,
        'user_id': cart.user.id if cart.user else None,
        'cart_created_at': timezone.now(),
    }
    
    return render(request, 'cart/cart.html', context)

@require_POST
def add_to_cart(request, product_id):
    """Добавление изделия в корзину"""
    product = get_object_or_404(Product, id=product_id, status='active')
    
    # Проверяем, запрос AJAX или обычный
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Проверка доступности
    if not product.is_available():
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'Товар недоступен для заказа'})
        messages.error(request, 'Товар недоступен для заказа')
        return redirect('product_detail', product_id=product_id)
    
    # Получаем количество из формы
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = 1
    
    if quantity <= 0:
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'Количество должно быть положительным числом'})
        messages.error(request, 'Количество должно быть положительным числом')
        return redirect('product_detail', product_id=product_id)
    
    # Проверяем наличие достаточного количества
    if product.stock_quantity < quantity:
        if is_ajax:
            return JsonResponse({'success': False, 'message': f'Недостаточно изделий в наличии. Доступно: {product.stock_quantity} шт.'})
        messages.error(request, f'Недостаточно изделий в наличии. Доступно: {product.stock_quantity} шт.')
        return redirect('product_detail', product_id=product_id)
    
    cart = get_or_create_cart(request)

    # Проверяем, есть ли уже такое изделие в корзине
    cart_item = CartItem.objects.filter(cart=cart, product=product).first()

    if cart_item:
        # Если изделие уже есть в корзине, увеличиваем количество
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock_quantity:
            if is_ajax:
                return JsonResponse({'success': False, 'message': f'Нельзя добавить больше изделий, чем есть в наличии. Уже в корзине: {cart_item.quantity} шт.'})
            messages.error(request, f'Нельзя добавить больше изделий, чем есть в наличии. Уже в корзине: {cart_item.quantity} шт.')
            return redirect('product_detail', product_id=product_id)
        else:
            cart_item.quantity = new_quantity
            cart_item.save()
    else:
        # Создаем новый элемент корзины
        if quantity > product.stock_quantity:
            if is_ajax:
                return JsonResponse({'success': False, 'message': f'Недостаточно изделий в наличии. Доступно: {product.stock_quantity} шт.'})
            messages.error(request, f'Недостаточно изделий в наличии. Доступно: {product.stock_quantity} шт.')
            return redirect('product_detail', product_id=product_id)
        else:
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity
            )
    
    # Получаем обновленную информацию о корзине
    item_count = cart.item_count()
    total = cart.calculate_total()
    
    # Если AJAX запрос, возвращаем JSON
    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': 'Товар добавлен в корзину',
            'item_count': item_count,
            'total': float(total)
        })
    
    # Для обычного запроса возвращаем пользователя на страницу изделия
    return redirect('product_detail', product_id=product_id)

@require_POST
def update_cart_item(request, item_id):
    """Обновление количества изделий в корзине"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    # Проверяем, запрос AJAX или обычный
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = 1
    
    if quantity <= 0:
        # Если количество 0 или меньше, удаляем изделие
        product_name = cart_item.product.name
        cart_item.delete()
        
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': f'Товар "{product_name}" удален из корзины',
                'item_count': cart.item_count(),
                'total': float(cart.calculate_total())
            })
        
        messages.success(request, f'Товар "{product_name}" удален из корзины')
    else:
        # Проверяем доступность
        if quantity > cart_item.product.stock_quantity:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': f'Недостаточно изделий в наличии. Доступно: {cart_item.product.stock_quantity} шт.'
                })
            
            messages.error(request, f'Недостаточно изделий в наличии. Доступно: {cart_item.product.stock_quantity} шт.')
        else:
            cart_item.quantity = quantity
            cart_item.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Количество изделий обновлено',
                    'item_count': cart.item_count(),
                    'total': float(cart.calculate_total())
                })
    
    # Для обычного запроса возвращаем редирект
    return redirect('cart_view')

@require_POST
def remove_from_cart(request, item_id):
    """Удаление изделия из корзины"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    product_name = cart_item.product.name
    cart_item.delete()
    
    # Проверяем, запрос AJAX или обычный
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': f'Изделие "{product_name}" удалено из корзины',
            'item_count': cart.item_count(),
            'total': float(cart.calculate_total())
        })
    
    messages.success(request, f'Изделие "{product_name}" удалено из корзины')
    return redirect('cart_view')

@require_POST
def clear_cart(request):
    """Очистка всей корзины"""
    cart = get_or_create_cart(request)
    item_count = cart.items.count()
    cart.clear()
    
    messages.success(request, f'Корзина очищена ({item_count} изделиеов удалено)')
    return redirect('cart_view')

def cart_summary(request):
    """Мини-корзина для отображения в шапке (AJAX)"""
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product').all()
    item_count = cart.item_count()
    total = cart.calculate_total()
    
    # Собираем информацию о изделиеах в корзине для отображения
    cart_items = []
    for item in items:
        cart_items.append({
            'id': item.id,  # ID элемента корзины (не продукта)
            'product_id': item.product.id,
            'name': item.product.name,
            'quantity': item.quantity,
            'price': float(item.product.price),
            'subtotal': float(item.calculate_subtotal()),
            'image': item.product.get_main_image().url if item.product.get_main_image() else None,
            'url': f'/products/{item.product.id}/',
            'stock_quantity': item.product.stock_quantity,
            'is_available': item.is_available()
        })
    
    return JsonResponse({
        'item_count': item_count,
        'total': float(total),
        'items': cart_items
    })

def checkout(request):
    """Переход к оформлению заказа"""
    cart = get_or_create_cart(request)
    
    # Проверяем, есть ли изделия в корзине
    if not cart.items.exists():
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('cart_view')
    
    # Проверяем доступность всех изделий
    unavailable_items = []
    for item in cart.items.all():
        if not item.is_available():
            unavailable_items.append(item)
    
    if unavailable_items:
        messages.error(request, 'Некоторые изделия в корзине недоступны. Пожалуйста, проверьте корзину.')
        return redirect('cart_view')
    
    # Перенаправляем на страницу оформления заказа
    return redirect('orders:checkout')
