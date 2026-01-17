from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.core.exceptions import ValidationError
import json

from products.models import Product, Category
from cart.models import Cart, CartItem
from .models import ProductTemplate, CustomOrderSpecification
from .forms import CustomOrderForm

def custom_order_constructor(request):
    """Главная страница конструктора индивидуальных заказов"""
    # Получаем все товары, которые можно кастомизировать
    customizable_products = Product.objects.filter(
        can_be_customized=True,
        status='active'
    ).select_related('category', 'master').order_by('-created_at')

    # Получаем категории товаров
    categories = Category.objects.filter(
        products__can_be_customized=True,
        products__status='active'
    ).distinct().order_by('name')

    context = {
        'customizable_products': customizable_products,
        'categories': categories,
        'title': 'Индивидуальные заказы'
    }

    return render(request, 'custom_orders/constructor_main.html', context)

@login_required
def custom_order_create(request, product_id):
    """Создание кастомного заказа"""
    product = get_object_or_404(Product, id=product_id, can_be_customized=True, status='active')
    
    # Получаем или создаем шаблон
    template, created = ProductTemplate.objects.get_or_create(
        product=product,
        defaults={
            'name': f"Шаблон {product.name}",
            'base_price': product.price,
            'base_production_days': product.production_time_days or 5,
        }
    )
    
    # Обновляем конфигурацию с динамическими опциями
    template.update_configuration_with_dynamic_options()
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            selections = data.get('selections', {})
            customer_notes = data.get('customer_notes', '')
            
            # Валидация выбора
            errors = template.validate_selections(selections)
            if errors:
                return JsonResponse({'success': False, 'errors': errors}, status=400)
            
            # Рассчитываем стоимость и срок
            total_price = template.calculate_price(selections)
            production_days = template.calculate_production_time(selections)
            
            # Создаем спецификацию
            with transaction.atomic():
                # Создаем элемент корзины
                cart, _ = Cart.objects.get_or_create(user=request.user)
                
                cart_item = CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=1,
                )
                
                # Обновляем цену в корзине на кастомную
                cart_item.price = total_price
                cart_item.save()
                
                # Создаем спецификацию кастомного заказа
                specification = CustomOrderSpecification.objects.create(
                    order_item=cart_item,
                    template=template,
                    user=request.user,
                    configuration={'selections': selections},
                    total_price=total_price,
                    production_days=production_days,
                    customer_notes=customer_notes,
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Кастомный заказ добавлен в корзину',
                'cart_item_id': cart_item.id,
                'total_price': total_price,
                'production_days': production_days,
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Неверный формат данных'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    # GET запрос - отображаем конструктор
    context = {
        'product': product,
        'template': template,
        'form': CustomOrderForm(),
    }
    
    return render(request, 'custom_orders/constructor.html', context)

@login_required
def custom_order_preview(request, specification_id):
    """Предпросмотр кастомного заказа"""
    specification = get_object_or_404(CustomOrderSpecification, id=specification_id, user=request.user)
    
    context = {
        'specification': specification,
        'summary': specification.get_configuration_summary(),
    }
    
    return render(request, 'custom_orders/preview.html', context)

@login_required
@require_POST
def calculate_custom_price(request):
    """Расчёт стоимости кастомного заказа (AJAX)"""
    try:
        data = json.loads(request.body)
        template_id = data.get('template_id')
        selections = data.get('selections', {})
        
        template = get_object_or_404(ProductTemplate, id=template_id)
        
        # Валидация
        errors = template.validate_selections(selections)
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        
        # Расчёт
        total_price = template.calculate_price(selections)
        production_days = template.calculate_production_time(selections)
        
        return JsonResponse({
            'success': True,
            'total_price': total_price,
            'production_days': production_days,
            'base_price': float(template.base_price),
            'currency': '₽',
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверный формат данных'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def my_custom_orders(request):
    """Список кастомных заказов пользователя"""
    specifications = CustomOrderSpecification.objects.filter(user=request.user).select_related(
        'template', 'order_item__order'
    ).order_by('-created_at')
    
    context = {
        'specifications': specifications,
    }
    
    return render(request, 'custom_orders/my_orders.html', context)

# Представления для мастера
@login_required
def master_custom_orders(request):
    """Список кастомных заказов для мастера"""
    if not request.user.is_master():
        messages.error(request, 'У вас нет прав для просмотра этой страницы')
        return redirect('home')
    
    # Получаем заказы на товары мастера
    specifications = CustomOrderSpecification.objects.filter(
        template__product__master=request.user
    ).select_related(
        'template', 'order_item__order', 'user'
    ).order_by('-created_at')
    
    # Разделяем по статусам
    pending_specifications = [s for s in specifications if not s.is_approved and not s.approval_notes]
    approved_specifications = [s for s in specifications if s.is_approved]
    rejected_specifications = [s for s in specifications if not s.is_approved and s.approval_notes]
    
    context = {
        'specifications': specifications,
        'pending_specifications': pending_specifications,
        'approved_specifications': approved_specifications,
        'rejected_specifications': rejected_specifications,
        'pending_count': len(pending_specifications),
        'approved_count': len(approved_specifications),
        'rejected_count': len(rejected_specifications),
    }
    
    return render(request, 'custom_orders/master_orders.html', context)

@login_required
@require_POST
def approve_custom_order(request, specification_id):
    """Согласование кастомного заказа мастером"""
    specification = get_object_or_404(CustomOrderSpecification, id=specification_id)
    
    if not request.user.is_master() or specification.template.product.master != request.user:
        messages.error(request, 'У вас нет прав для выполнения этого действия')
        return redirect('home')
    
    notes = request.POST.get('notes', '')
    specification.approve(notes)
    
    messages.success(request, 'Кастомный заказ успешно согласован')
    return redirect('master_custom_orders')

@login_required
@require_POST
def reject_custom_order(request, specification_id):
    """Отклонение кастомного заказа мастером"""
    specification = get_object_or_404(CustomOrderSpecification, id=specification_id)
    
    if not request.user.is_master() or specification.template.product.master != request.user:
        messages.error(request, 'У вас нет прав для выполнения этого действия')
        return redirect('home')
    
    notes = request.POST.get('notes', '')
    specification.reject(notes)
    
    messages.success(request, 'Кастомный заказ отклонён')
    return redirect('master_custom_orders')
