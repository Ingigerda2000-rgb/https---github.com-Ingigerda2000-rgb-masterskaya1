# materials/views.py - ПОЛНАЯ ВЕРСИЯ
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Sum, F, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
import json

from .models import Material, MaterialRecipe, MaterialReservation
from .forms import MaterialForm, MaterialRecipeForm, QuickMaterialForm
from .utils import MaterialManager, InsufficientMaterialError
from products.models import Product
from orders.models import Order, OrderItem

# ============================================================================
# КЛАССОВЫЕ ПРЕДСТАВЛЕНИЯ (CBV)
# ============================================================================

class MaterialListView(LoginRequiredMixin, ListView):
    """Список материалов мастера"""
    model = Material
    template_name = 'materials/material_list.html'
    context_object_name = 'materials'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Material.objects.filter(
            master=self.request.user,
            is_active=True
        ).select_related('master')
        
        # Поиск
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(color__icontains=search_query) |
                Q(supplier__icontains=search_query) |
                Q(texture__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
        
        # Фильтрация по статусу запаса
        stock_filter = self.request.GET.get('stock', '')
        if stock_filter == 'low':
            queryset = queryset.filter(
                current_quantity__lte=F('min_quantity'),
                current_quantity__gt=0
            )
        elif stock_filter == 'out':
            queryset = queryset.filter(current_quantity=0)
        elif stock_filter == 'warning':
            queryset = queryset.filter(
                current_quantity__lte=F('min_quantity') * Decimal('1.25'),
                current_quantity__gt=F('min_quantity')
            )
        
        # Сортировка
        sort_by = self.request.GET.get('sort', 'name')
        if sort_by == 'quantity_asc':
            queryset = queryset.order_by('current_quantity')
        elif sort_by == 'quantity_desc':
            queryset = queryset.order_by('-current_quantity')
        elif sort_by == 'value_desc':
            queryset = queryset.order_by(-(F('current_quantity') * F('price_per_unit')))
        elif sort_by == 'name_desc':
            queryset = queryset.order_by('-name')
        elif sort_by == 'updated':
            queryset = queryset.order_by('-updated_at')
        else:  # 'name' по умолчанию
            queryset = queryset.order_by('name')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        queryset = self.get_queryset()
        
        # Статистика
        context['total_materials'] = queryset.count()
        context['low_stock_count'] = queryset.filter(
            current_quantity__lte=F('min_quantity'),
            current_quantity__gt=0
        ).count()
        context['out_of_stock'] = queryset.filter(current_quantity=0).count()
        context['warning_stock_count'] = queryset.filter(
            current_quantity__lte=F('min_quantity') * Decimal('1.25'),
            current_quantity__gt=F('min_quantity')
        ).count()
        
        # Общая стоимость запасов
        total_value = queryset.aggregate(
            total=Sum(F('current_quantity') * F('price_per_unit'))
        )['total'] or Decimal('0')
        context['total_stock_value'] = total_value
        
        # Параметры фильтрации
        context['search_query'] = self.request.GET.get('search', '')
        context['stock_filter'] = self.request.GET.get('stock', '')
        context['sort_by'] = self.request.GET.get('sort', 'name')
        
        # Форма быстрого добавления
        context['quick_form'] = QuickMaterialForm()
        
        return context


class MaterialDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Детальная информация о материале"""
    model = Material
    template_name = 'materials/material_detail.html'
    context_object_name = 'material'
    
    def test_func(self):
        material = self.get_object()
        return material.master == self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        material = self.get_object()
        
        # Рецепты, в которых используется этот материал
        context['recipes'] = material.recipes.select_related('product')
        
        # История резервирований
        context['reservations'] = material.reservations.select_related(
            'order_item', 'order_item__order', 'order_item__product'
        ).order_by('-reserved_at')[:10]
        
        # Статистика использования
        context['consumption_stats'] = material.reservations.filter(
            status='consumed'
        ).aggregate(
            total_consumed=Sum('quantity'),
            total_cost=Sum(F('quantity') * F('price_per_unit'))
        )
        
        return context


class MaterialCreateView(LoginRequiredMixin, CreateView):
    """Создание нового материала"""
    model = Material
    form_class = MaterialForm
    template_name = 'materials/material_form.html'
    success_url = reverse_lazy('materials:material_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['master'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, '✅ Материал успешно создан')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление нового материала'
        context['submit_text'] = 'Создать материал'
        return context


class MaterialUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование материала"""
    model = Material
    form_class = MaterialForm
    template_name = 'materials/material_form.html'
    success_url = reverse_lazy('materials:material_list')
    
    def test_func(self):
        material = self.get_object()
        return material.master == self.request.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['master'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, '✅ Материал успешно обновлён')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование материала: {self.object.name}'
        context['submit_text'] = 'Сохранить изменения'
        return context


class MaterialDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление материала (мягкое удаление)"""
    model = Material
    template_name = 'materials/material_confirm_delete.html'
    success_url = reverse_lazy('materials:material_list')
    
    def test_func(self):
        material = self.get_object()
        return material.master == self.request.user
    
    def delete(self, request, *args, **kwargs):
        material = self.get_object()
        material.is_active = False
        material.save()
        messages.success(request, '✅ Материал успешно деактивирован')
        return redirect(self.success_url)


class MaterialRecipeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Добавление рецепта к товару"""
    model = MaterialRecipe
    form_class = MaterialRecipeForm
    template_name = 'materials/materialrecipe_form.html'
    
    def test_func(self):
        product_id = self.kwargs.get('product_id')
        product = get_object_or_404(Product, pk=product_id)
        return product.master == self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, pk=self.kwargs['product_id'])
        context['product'] = product
        context['title'] = f'Добавление рецепта для товара: {product.name}'
        context['existing_recipes'] = product.material_recipes.select_related('material')
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        product = get_object_or_404(Product, pk=self.kwargs['product_id'])
        kwargs['product'] = product
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, '✅ Рецепт материала успешно добавлен')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('products:product_detail', kwargs={'pk': self.kwargs['product_id']})


class MaterialRecipeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование рецепта материала"""
    model = MaterialRecipe
    form_class = MaterialRecipeForm
    template_name = 'materials/materialrecipe_form.html'
    
    def test_func(self):
        recipe = self.get_object()
        return recipe.product.master == self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.object.product
        context['title'] = f'Редактирование рецепта: {self.object.material.name}'
        context['submit_text'] = 'Сохранить изменения'
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product'] = self.object.product
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, '✅ Рецепт материала успешно обновлён')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('products:product_detail', kwargs={'pk': self.object.product.id})


class MaterialRecipeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление рецепта материала"""
    model = MaterialRecipe
    template_name = 'materials/materialrecipe_confirm_delete.html'
    
    def test_func(self):
        recipe = self.get_object()
        return recipe.product.master == self.request.user
    
    def delete(self, request, *args, **kwargs):
        recipe = self.get_object()
        product_id = recipe.product.id
        recipe.delete()
        messages.success(request, '✅ Рецепт материала успешно удалён')
        return redirect('products:product_detail', pk=product_id)


class LowStockAlertView(LoginRequiredMixin, ListView):
    """Просмотр материалов с низким запасом"""
    model = Material
    template_name = 'materials/low_stock_alerts.html'
    context_object_name = 'materials'
    
    def get_queryset(self):
        queryset = Material.objects.filter(
            master=self.request.user,
            is_active=True,
            current_quantity__lte=F('min_quantity')
        ).order_by('current_quantity')
        
        # Разделяем на полностью закончившиеся и низкий запас
        self.out_of_stock = queryset.filter(current_quantity=0)
        self.low_stock = queryset.filter(current_quantity__gt=0)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['out_of_stock'] = self.out_of_stock
        context['low_stock'] = self.low_stock
        context['total_low_stock'] = self.low_stock.count()
        context['total_out_of_stock'] = self.out_of_stock.count()
        return context


class MaterialReservationsView(LoginRequiredMixin, ListView):
    """Просмотр резервирований материалов"""
    model = MaterialReservation
    template_name = 'materials/reservations.html'
    context_object_name = 'reservations'
    paginate_by = 20
    
    def get_queryset(self):
        # Получаем резервирования для материалов мастера
        status_filter = self.request.GET.get('status', '')
        
        queryset = MaterialReservation.objects.filter(
            material__master=self.request.user
        ).select_related(
            'material', 
            'order_item', 
            'order_item__order', 
            'order_item__product'
        ).order_by('-reserved_at')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика по статусам
        reservations = MaterialReservation.objects.filter(
            material__master=self.request.user
        )
        
        context['status_stats'] = reservations.values('status').annotate(
            count=Count('id'),
            total_quantity=Sum('quantity')
        )
        
        context['status_filter'] = self.request.GET.get('status', '')
        
        return context


# ============================================================================
# ФУНКЦИОНАЛЬНЫЕ ПРЕДСТАВЛЕНИЯ (FBV)
# ============================================================================

@login_required
def material_report(request):
    """Отчет по материалам для мастера"""
    if request.user.role != 'master':
        messages.error(request, '❌ Эта страница доступна только мастерам')
        return redirect('home')
    
    # Получаем отчёт через MaterialManager
    report = MaterialManager.get_material_report(request.user.id)
    
    # Получаем материалы для отображения в карточках
    materials = Material.objects.filter(
        master=request.user,
        is_active=True
    ).order_by('name')
    
    # Статистика через MaterialManager
    stats = MaterialManager.get_material_statistics(request.user.id)
    
    # Список для заказа
    reorder_list = MaterialManager.generate_reorder_list(request.user.id)
    
    context = {
        'report': report,
        'materials': materials,
        'stats': stats,
        'reorder_list': reorder_list,
    }
    
    return render(request, 'materials/report.html', context)


@login_required
def quick_add_material(request):
    """Быстрое добавление материала (AJAX)"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = QuickMaterialForm(request.POST)
        
        if form.is_valid():
            name = form.cleaned_data['name']
            current_quantity = form.cleaned_data['current_quantity']
            unit = form.cleaned_data['unit']
            
            # Создаём материал
            material = Material.objects.create(
                master=request.user,
                name=name,
                current_quantity=current_quantity,
                unit=unit,
                min_quantity=Decimal('0'),
                price_per_unit=Decimal('0')
            )
            
            return JsonResponse({
                'success': True,
                'id': str(material.id),
                'name': material.name,
                'quantity': str(material.current_quantity),
                'unit': material.get_unit_display(),
                'is_low_stock': material.is_low_stock,
                'status_class': 'danger' if material.current_quantity == 0 else 'warning' if material.is_low_stock else 'success'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def update_material_quantity(request, pk):
    """Быстрое обновление количества материала (AJAX)"""
    material = get_object_or_404(Material, pk=pk, master=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action', 'set')
        quantity_str = request.POST.get('quantity', '0')
        
        try:
            quantity = Decimal(quantity_str)
            
            if action == 'add':
                material.current_quantity += quantity
            elif action == 'subtract':
                material.current_quantity = max(Decimal('0'), material.current_quantity - quantity)
            elif action == 'set':
                material.current_quantity = quantity
            
            material.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'quantity': str(material.current_quantity),
                    'is_low_stock': material.is_low_stock,
                    'status': 'out' if material.current_quantity == 0 else 'low' if material.is_low_stock else 'ok',
                    'status_text': 'Нет в наличии' if material.current_quantity == 0 else 'Низкий запас' if material.is_low_stock else 'В норме',
                    'status_class': 'danger' if material.current_quantity == 0 else 'warning' if material.is_low_stock else 'success',
                    'stock_value': str(material.stock_value),
                })
            else:
                messages.success(request, f'✅ Количество материала "{material.name}" обновлено')
                return redirect('materials:material_list')
                
        except (ValueError, TypeError) as e:
            error_msg = f'❌ Ошибка: неверный формат количества'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            else:
                messages.error(request, error_msg)
                return redirect('materials:material_list')
    
    return redirect('materials:material_list')


@login_required
def consume_material(request, pk):
    """Ручное списание материала"""
    material = get_object_or_404(Material, pk=pk, master=request.user)
    
    if request.method == 'POST':
        quantity_str = request.POST.get('quantity', '0')
        reason = request.POST.get('reason', '')
        notes = request.POST.get('notes', '')
        
        try:
            quantity = Decimal(quantity_str)
            
            if quantity <= 0:
                raise ValueError("Количество должно быть больше 0")
            
            if quantity > material.current_quantity:
                raise ValueError("Недостаточно материала на складе")
            
            # Создаём запись о ручном списании
            reservation = MaterialReservation.objects.create(
                material=material,
                order_item=None,  # Ручное списание, не связанное с заказом
                quantity=quantity,
                status='consumed',
                consumed_at=timezone.now(),
                notes=f"Ручное списание. Причина: {reason}. {notes}"
            )
            
            # Списание материала
            material.current_quantity -= quantity
            material.save()
            
            messages.success(request, f'✅ Списано {quantity} {material.get_unit_display()} материала "{material.name}"')
            
        except (ValueError, TypeError) as e:
            messages.error(request, f'❌ Ошибка: {str(e)}')
    
    return redirect('materials:material_list')


@login_required
def get_material_stats(request):
    """Получить статистику по материалам (AJAX)"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        stats = MaterialManager.get_material_statistics(request.user.id)
        return JsonResponse({'success': True, 'stats': stats})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def export_materials_csv(request):
    """Экспорт материалов в CSV"""
    from django.http import HttpResponse
    import csv
    
    if request.user.role != 'master':
        return redirect('home')
    
    materials = Material.objects.filter(master=request.user, is_active=True)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="materials_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Название', 'Количество', 'Ед. изм.', 'Мин. запас', 'Цена за ед.', 
                     'Стоимость запаса', 'Цвет', 'Поставщик', 'Статус'])
    
    for material in materials:
        status = 'Нет в наличии' if material.current_quantity == 0 else \
                 'Низкий запас' if material.is_low_stock else 'В норме'
        
        writer.writerow([
            material.name,
            str(material.current_quantity),
            material.get_unit_display(),
            str(material.min_quantity),
            str(material.price_per_unit),
            str(material.stock_value),
            material.color or '',
            material.supplier or '',
            status
        ])
    
    return response
class MaterialDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Детальная информация о материале"""
    model = Material
    template_name = 'materials/material_detail.html'
    context_object_name = 'material'
    
    def test_func(self):
        material = self.get_object()
        return material.master == self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        material = self.get_object()
        
        # Рецепты, в которых используется этот материал
        context['recipes'] = material.recipes.select_related('product')
        
        # История резервирований
        context['reservations'] = material.reservations.select_related(
            'order_item', 'order_item__order', 'order_item__product'
        ).order_by('-reserved_at')[:10]
        
        # Статистика использования
        from django.db.models import Sum, F
        consumption_stats = material.reservations.filter(
            status='consumed'
        ).aggregate(
            total_consumed=Sum('quantity'),
            total_cost=Sum(F('quantity') * F('material__price_per_unit'))
        )
        context['consumption_stats'] = consumption_stats
        
        return context