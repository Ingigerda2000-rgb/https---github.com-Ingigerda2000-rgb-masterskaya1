from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, UpdateView
from django.views.generic.edit import FormView
from django.db.models import Q
from django.http import JsonResponse
from django.db.models import Count

from .models import Order, OrderStatusHistory, ORDER_STATUS_CHOICES
from .forms import OrderStatusUpdateForm, CustomerCancelOrderForm, StatusFilterForm


@method_decorator(login_required, name='dispatch')
class OrderListView(ListView):
    """Список заказов текущего пользователя"""
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


@method_decorator(login_required, name='dispatch')
class OrderDetailView(DetailView):
    """Детальная страница заказа"""
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        # Пользователь может видеть только свои заказы
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_form'] = CustomerCancelOrderForm()
        context['status_history'] = self.object.status_history.all().order_by('-changed_at')[:5]
        context['timeline_events'] = self.object.get_timeline_events()
        context['ORDER_STATUS_CHOICES'] = ORDER_STATUS_CHOICES
        return context


@method_decorator(login_required, name='dispatch')
class OrderCancelView(FormView):
    """Отмена заказа покупателем"""
    form_class = CustomerCancelOrderForm
    template_name = 'orders/cancel_order.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order'] = get_object_or_404(Order, id=self.kwargs['pk'])
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        try:
            form.save()
            messages.success(self.request, 'Заказ успешно отменен')
            return redirect('orders:order_detail', pk=self.kwargs['pk'])
        except Exception as e:
            messages.error(self.request, f'Ошибка при отмене заказа: {str(e)}')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = get_object_or_404(Order, id=self.kwargs['pk'])
        return context


@method_decorator(login_required, name='dispatch')
class OrderStatusUpdateView(UpdateView):
    """Изменение статуса заказа мастером/администратором"""
    model = Order
    form_class = OrderStatusUpdateForm
    template_name = 'orders/update_status.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order'] = self.object
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        try:
            form.save()
            messages.success(
                self.request, 
                f'Статус заказа #{self.object.id} изменен на "{self.object.get_status_display()}"'
            )
            return redirect('orders:order_detail', pk=self.object.id)
        except Exception as e:
            messages.error(self.request, f'Ошибка: {str(e)}')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_history'] = self.object.status_history.all().order_by('-changed_at')[:10]
        context['next_possible_statuses'] = self.object.get_next_possible_statuses(self.request.user)
        return context
    
    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()
        
        # Проверяем права доступа
        if not (request.user.is_staff or
                (request.user.is_master and order.is_master_order(request.user))):
            messages.error(request, 'У вас нет прав для изменения статуса этого заказа')
            return redirect('orders:order_detail', pk=order.id)
        
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class OrderTimelineView(DetailView):
    """Полная хронология статусов заказа"""
    model = Order
    template_name = 'orders/order_timeline.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        # Пользователь может видеть только свои заказы
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class MasterOrdersView(ListView):
    """Список заказов для мастера с фильтрацией"""
    model = Order
    template_name = 'orders/master_orders.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        # Мастер видит только заказы со своими товарами
        queryset = Order.objects.filter(
            items__product__master=self.request.user
        ).distinct()
        
        # Применяем фильтры
        form = StatusFilterForm(self.request.GET)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            search = form.cleaned_data.get('search')
            
            if status:
                queryset = queryset.filter(status=status)
            
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)
            
            if search:
                queryset = queryset.filter(
                    Q(id__icontains=search) |
                    Q(customer_name__icontains=search) |
                    Q(customer_email__icontains=search) |
                    Q(customer_phone__icontains=search) |
                    Q(tracking_number__icontains=search)
                )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = StatusFilterForm(self.request.GET or None)
        context['status_counts'] = self.get_status_counts()
        context['ORDER_STATUS_CHOICES'] = ORDER_STATUS_CHOICES
        return context
    
    def get_status_counts(self):
        """Возвращает количество заказов по каждому статусу"""
        return Order.objects.filter(
            items__product__master=self.request.user
        ).values('status').annotate(
            count=Count('id')
        ).order_by('status')


@login_required
def update_order_status_ajax(request, pk):
    """AJAX-метод для быстрого изменения статуса"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=pk)
        
        # Проверяем права доступа
        if not (request.user.is_staff or
                (request.user.is_master and order.is_master_order(request.user))):
            return JsonResponse({
                'success': False,
                'error': 'Недостаточно прав'
            })
        
        new_status = request.POST.get('status')
        comment = request.POST.get('comment', '')
        
        if new_status:
            try:
                order.update_status(
                    new_status=new_status,
                    user=request.user,
                    comment=comment
                )
                return JsonResponse({
                    'success': True,
                    'status': order.get_status_display(),
                    'status_class': order.status,
                    'status_color': order.status_color,
                    'status_icon': order.status_icon,
                    'progress': order.get_status_progress()
                })
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def order_status_counts_api(request):
    """API для получения статистики по статусам"""
    if request.user.is_staff:
        queryset = Order.objects.all()
    elif request.user.is_master:
        queryset = Order.objects.filter(
            items__product__master=request.user
        ).distinct()
    else:
        queryset = Order.objects.filter(user=request.user)
    
    counts = queryset.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    data = {
        'total': queryset.count(),
        'statuses': list(counts),
        'status_display': dict(ORDER_STATUS_CHOICES)
    }
    
    return JsonResponse(data)