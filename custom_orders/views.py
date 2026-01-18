from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
import json
from products.models import Category

from products.models import Product, Category
from cart.models import Cart, CartItem
from .models import ProductTemplate, CustomOrderSpecification
from .forms import CustomOrderForm

def constructor_main(request):
    """Главная страница конструктора (шаг 0)"""
    # Очищаем сессию при начале нового заказа
    if 'constructor_data' in request.session:
        del request.session['constructor_data']
    
    # Получаем рекомендуемые шаблоны
    featured_templates = ProductTemplate.objects.filter(
        is_active=True, 
        is_featured=True
    )[:6]
    
    return render(request, 'custom_orders/constructor_start.html', {
        'featured_templates': featured_templates,
        'title': 'Конструктор индивидуальных вещей'
    })

def constructor_step(request, step, template_id=None):
    """Обработка шага конструктора"""
    steps = [
        'category',      # Шаг 1: Выбор категории
        'product',       # Шаг 2: Выбор товара
        'configuration', # Шаг 3: Настройка
        'description',   # Шаг 4: Описание идеи
        'options',       # Шаг 5: Дополнительно
        'summary'        # Шаг 6: Итог
    ]

    step_display_names = {
        'category': 'Категория',
        'product': 'Товар',
        'configuration': 'Настройка',
        'description': 'Описание',
        'options': 'Дополнительно',
        'summary': 'Итог'
    }

    if step < 1 or step > len(steps):
        return redirect('custom_orders:constructor_main')

    step_name = steps[step - 1]
    step_display_name = step_display_names.get(step_name, step_name)
    
    # Получаем данные из сессии
    constructor_data = request.session.get('constructor_data', {})
    
    # Если передан template_id, сохраняем его
    if template_id and step_name == 'product':
        template = get_object_or_404(ProductTemplate, id=template_id, is_active=True)
        constructor_data['template_id'] = template_id
        constructor_data['product_id'] = template.product.id
        constructor_data['product_name'] = template.product.name
        constructor_data['base_price'] = float(template.base_price)
        constructor_data['base_days'] = template.base_production_days
        request.session['constructor_data'] = constructor_data
        request.session.modified = True
    
    context = {
        'current_step': step,
        'total_steps': len(steps),
        'step_name': step_name,
        'step_display_name': step_display_name,
        'steps': steps,
        'constructor_data': constructor_data,
    }
    
    # Добавляем данные в зависимости от шага
    if step_name == 'category':
        categories = Category.objects.filter(
            products__can_be_customized=True,
            products__status='active'
        ).distinct().order_by('name')
        context['categories'] = categories
    
    elif step_name == 'product':
        category_id = constructor_data.get('category_id')
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                category_ids = category.get_all_descendant_ids()
                templates = ProductTemplate.objects.filter(
                    product__category_id__in=category_ids,
                    is_active=True
                )
            except Category.DoesNotExist:
                templates = ProductTemplate.objects.filter(is_active=True)
        else:
            templates = ProductTemplate.objects.filter(is_active=True)
        context['templates'] = templates
    
    elif step_name == 'configuration' and constructor_data.get('template_id'):
        template = get_object_or_404(ProductTemplate, id=constructor_data['template_id'])
        from materials.models import Material

        # Получаем доступные материалы
        materials = Material.objects.filter(is_active=True)

        # Добавляем рассчитанную стоимость и требуемое количество для каждого материала
        for material in materials:
            # Определяем базовое требуемое количество в зависимости от единицы измерения
            if material.unit == 'g':
                base_required = 840  # граммы
            elif material.unit == 'm':
                base_required = 2  # метры
            elif material.unit == 'kg':
                base_required = 0.84  # килограммы (840г)
            elif material.unit == 'cm':
                base_required = 200  # сантиметры
            else:
                base_required = 1  # по умолчанию

            material.required_quantity = base_required
            material.calculated_price = material.price_per_unit * base_required

        # Обновляем конфигурацию шаблона
        template.update_configuration_with_dynamic_options()
        
        # Данные для размеров и цветов
        sizes = [
            {'value': 'XS', 'label': 'XS', 'multiplier': 0.8},
            {'value': 'S', 'label': 'S', 'multiplier': 0.9},
            {'value': 'M', 'label': 'M', 'multiplier': 1.0},
            {'value': 'L', 'label': 'L', 'multiplier': 1.1},
            {'value': 'XL', 'label': 'XL', 'multiplier': 1.2},
            {'value': 'custom', 'label': 'Индивидуальный', 'multiplier': 1.15},
        ]
        
        colors = [
            {'id': 1, 'name': 'Белый', 'hex': '#FFFFFF'},
            {'id': 2, 'name': 'Черный', 'hex': '#000000'},
            {'id': 3, 'name': 'Серый', 'hex': '#808080'},
            {'id': 4, 'name': 'Бежевый', 'hex': '#F5F5DC'},
            {'id': 5, 'name': 'Коричневый', 'hex': '#A52A2A'},
            {'id': 6, 'name': 'Красный', 'hex': '#FF0000'},
            {'id': 7, 'name': 'Розовый', 'hex': '#FFC0CB'},
            {'id': 8, 'name': 'Фиолетовый', 'hex': '#800080'},
            {'id': 9, 'name': 'Синий', 'hex': '#0000FF'},
            {'id': 10, 'name': 'Зеленый', 'hex': '#00FF00'},
            {'id': 11, 'name': 'Желтый', 'hex': '#FFFF00'},
            {'id': 12, 'name': 'Оранжевый', 'hex': '#FFA500'},
            {'id': 13, 'name': 'Свой вариант', 'hex': '#CCCCCC'},
        ]
        
        # Calculate production times for different urgencies
        base_days = template.base_production_days
        fast_days = max(int(base_days * 0.7), 1)
        express_days = max(int(base_days * 0.5), 1)

        context.update({
            'template': template,
            'materials': materials,
            'config': template.configuration if isinstance(template.configuration, dict) else {},
            'sizes': sizes,
            'colors': colors,
            'selected_size': constructor_data.get('size'),
            'selected_color': constructor_data.get('color'),
            'selected_materials': constructor_data.get('materials', []),
            'selected_urgency': constructor_data.get('urgency', 'standard'),
            'base_days': base_days,
            'fast_days': fast_days,
            'express_days': express_days,
        })
    
    elif step_name == 'description':
        context['description'] = constructor_data.get('description', '')
    
    elif step_name == 'options':
        context['options'] = constructor_data.get('options', {})
    
    elif step_name == 'summary':
        template_id = constructor_data.get('template_id')
        if not template_id:
            return redirect('custom_orders:constructor_main')

        template = get_object_or_404(ProductTemplate, id=template_id)

        # Получаем выбранные материалы и опции
        selected_materials = constructor_data.get('materials', [])
        selected_options = constructor_data.get('options', {})

        # Рассчитываем суммы
        total_materials = sum(float(material.get('price', 0)) for material in selected_materials)
        total_options = sum(float(option.get('price', 0)) for option in selected_options.values() if option.get('selected'))

        # Рассчитываем итоговую стоимость БЕЗ доставки
        total_price = float(template.base_price) + total_materials + total_options

        # Учет срочности
        urgency = constructor_data.get('urgency', 'standard')
        if urgency == 'fast':
            total_price *= 1.2  # +20%
        elif urgency == 'express':
            total_price *= 1.5  # +50%

        # РАССЧИТЫВАЕМ СРОКИ с учетом срочности
        base_days = int(constructor_data.get('base_days', template.base_production_days) or template.base_production_days or 5)
        additional_days = int(constructor_data.get('additional_days', 0))

        if urgency == 'fast':
            production_days = int((base_days + additional_days) * 0.7)  # На 30% быстрее
        elif urgency == 'express':
            production_days = int((base_days + additional_days) * 0.5)  # На 50% быстрее
        else:
            production_days = base_days + additional_days

        # Calculate surcharge amounts
        surcharge_fast = round(template.base_price * 0.2, 2) if urgency == 'fast' else 0
        surcharge_express = round(template.base_price * 0.5, 2) if urgency == 'express' else 0

        context.update({
            'template': template,
            'selected_materials': selected_materials,
            'selected_options': selected_options,
            'selected_size': constructor_data.get('size'),
            'selected_color': constructor_data.get('color'),
            'description': constructor_data.get('description', ''),
            'total_price': round(total_price, 2),
            'total_materials': total_materials,
            'total_options': total_options,
            'production_days': max(production_days, 1),
            'urgency': urgency,
            'additional_days': additional_days,
            'surcharge_fast': surcharge_fast,
            'surcharge_express': surcharge_express,
        })
    
    return render(request, f'custom_orders/constructor_{step_name}.html', context)

@login_required
@require_POST
def save_constructor_step(request):
    """Сохранение данных шага конструктора (AJAX)"""
    try:
        data = json.loads(request.body)
        step = data.get('step')
        step_data = data.get('data', {})
        
        constructor_data = request.session.get('constructor_data', {})
        
        # Сохраняем данные шага
        if step == 'category':
            constructor_data['category_id'] = step_data.get('category_id')
            constructor_data['category_name'] = step_data.get('category_name')
        
        elif step == 'product':
            constructor_data['template_id'] = step_data.get('template_id')
            constructor_data['product_name'] = step_data.get('product_name')
            constructor_data['base_price'] = step_data.get('base_price')
            constructor_data['base_days'] = step_data.get('base_days')
        
        elif step == 'configuration':
            constructor_data['size'] = step_data.get('size')
            constructor_data['color'] = step_data.get('color')
            constructor_data['materials'] = step_data.get('materials', [])
            constructor_data['urgency'] = step_data.get('urgency', 'standard')
            constructor_data['urgency_multiplier'] = step_data.get('urgency_multiplier', 1.0)
            
            # Рассчитываем дополнительные дни и стоимость за материалы
            additional_days = 0
            for material in step_data.get('materials', []):
                additional_days += material.get('additional_days', 0)
            constructor_data['additional_days'] = additional_days
        
        elif step == 'description':
            constructor_data['description'] = step_data.get('description')
            constructor_data['references'] = step_data.get('references', [])
        
        elif step == 'options':
            constructor_data['options'] = step_data.get('options', {})
        
        request.session['constructor_data'] = constructor_data
        request.session.modified = True
        
        return JsonResponse({'success': True, 'data': constructor_data})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def finalize_custom_order(request):
    """Финальное оформление кастомного заказа - добавление в корзину"""
    try:
        constructor_data = request.session.get('constructor_data', {})
        
        if not constructor_data.get('template_id'):
            return JsonResponse({'success': False, 'error': 'Не выбран товар'}, status=400)
        
        template = get_object_or_404(ProductTemplate, id=constructor_data['template_id'])
        if not template.is_active:
            return JsonResponse({'success': False, 'error': 'Шаблон не доступен'}, status=400)

        product = template.product
        if product.status != 'active':
            return JsonResponse({'success': False, 'error': 'Товар не доступен'}, status=400)
        
        # Рассчитываем итоговую стоимость
        total_price = float(template.base_price)
        
        # Добавляем стоимость материалов
        selected_materials = constructor_data.get('materials', [])
        for material_data in selected_materials:
            total_price += float(material_data.get('price', 0))
        
        # Добавляем стоимость опций
        selected_options = constructor_data.get('options', {})
        for option in selected_options.values():
            if option.get('selected'):
                total_price += float(option.get('price', 0))
        
        # Учет срочности
        urgency = constructor_data.get('urgency', 'standard')
        if urgency == 'fast':
            total_price *= 1.2
        elif urgency == 'express':
            total_price *= 1.5
        
        # Рассчитываем сроки
        base_days = constructor_data.get('base_days', template.base_production_days)
        additional_days = constructor_data.get('additional_days', 0)
        
        if urgency == 'fast':
            production_days = int((base_days + additional_days) * 0.7)
        elif urgency == 'express':
            production_days = int((base_days + additional_days) * 0.5)
        else:
            production_days = base_days + additional_days
        
        # Создаем заказ
        with transaction.atomic():
            # Создаем или получаем корзину пользователя
            cart, _ = Cart.objects.get_or_create(user=request.user)
            
            # Создаем элемент корзины
            try:
                cart_item = CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=1,
                    price=total_price  # Устанавливаем кастомную цену
                )
            except IntegrityError:
                return JsonResponse({'success': False, 'error': 'Этот товар уже в корзине'})
            
            # Создаем спецификацию кастомного заказа
            specification = CustomOrderSpecification.objects.create(
                order_item=None,
                template=template,
                user=request.user,
                configuration={
                    'constructor_data': constructor_data,
                    'selections': {
                        'size': constructor_data.get('size'),
                        'color': constructor_data.get('color'),
                        'materials': constructor_data.get('materials', []),
                        'options': constructor_data.get('options', {}),
                        'description': constructor_data.get('description', ''),
                        'urgency': constructor_data.get('urgency', 'standard'),
                    }
                },
                total_price=total_price,
                production_days=max(production_days, 1),
                customer_notes=constructor_data.get('description', ''),
            )
        
        # Очищаем сессию
        if 'constructor_data' in request.session:
            del request.session['constructor_data']
        
        return JsonResponse({
            'success': True,
            'message': 'Кастомный заказ добавлен в корзину',
            'total_price': total_price,
            'production_days': production_days,
            'redirect_url': '/cart/'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Старые функции (оставляем для совместимости)
def custom_order_constructor(request):
    selected_category_id = request.session.get('custom_order_category')
    customizable_products = Product.objects.filter(can_be_customized=True, status='active')
    categories = Category.objects.filter(
        products__can_be_customized=True,
        products__status='active'
    ).distinct().order_by('name')

    if selected_category_id:
        customizable_products = customizable_products.filter(category_id=selected_category_id)

    context = {
        'customizable_products': customizable_products,
        'categories': categories,
        'title': 'Индивидуальные заказы',
    }
    return render(request, 'custom_orders/constructor_main.html', context)

@login_required
def custom_order_create(request, product_id):
    """Создание кастомного заказа (старая версия)"""
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

def choose_category(request):
    categories = Category.objects.filter(
        products__can_be_customized=True,
        products__status='active'
    ).distinct().order_by('name')

    if request.method == 'POST':
        selected_category_id = request.POST.get('category')
        if selected_category_id:
            request.session['custom_order_category'] = selected_category_id
            return redirect('custom_orders:custom_order_constructor')

    context = {
        'categories': categories,
        'title': 'Выбор категории для индивидуального заказа'
    }
    return render(request, 'custom_orders/choose_category.html', context)

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
def edit_custom_order(request, specification_id):
    """Редактирование кастомного заказа мастером"""
    specification = get_object_or_404(CustomOrderSpecification, id=specification_id)

    if not request.user.is_master() or specification.template.product.master != request.user:
        messages.error(request, 'У вас нет прав для выполнения этого действия')
        return redirect('home')

    if request.method == 'POST':
        form = CustomOrderForm(request.POST, instance=specification)
        if form.is_valid():
            form.save()
            messages.success(request, 'Кастомный заказ успешно обновлён')
            return redirect('master_custom_orders')
    else:
        form = CustomOrderForm(instance=specification)

    context = {
        'form': form,
        'specification': specification,
        'title': f'Редактирование заказа #{specification.order_item.order.order_number}'
    }

    return render(request, 'custom_orders/edit_order.html', context)

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
