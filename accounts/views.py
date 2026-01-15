from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordChangeForm
from .models import User
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from .tokens import email_confirmation_token
from django.contrib.auth import logout as auth_logout
from .forms import CustomAuthenticationForm
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from products.models import Product, Category
# ============================================================================
# ГЛАВНАЯ СТРАНИЦА
# ============================================================================

def home_view(request):
    """Главная страница мастерской"""
    # Получаем все активные товары
    products = Product.objects.filter(status='active').order_by('-created_at')

    # Поиск по названию и описанию
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Фильтр по категории
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    # Фильтр по технике
    technique = request.GET.get('technique')
    if technique:
        products = products.filter(technique=technique)

    # Фильтр по цене
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Пагинация
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 12)  # 12 товаров на странице

    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    # Получаем фильтры для формы
    categories = Category.objects.all()
    techniques = Product.objects.filter(status='active').exclude(
        technique__isnull=True
    ).exclude(technique='').values_list('technique', flat=True).distinct()

    context = {
        'products': products_page,
        'categories': categories,
        'techniques': techniques,
        'search_query': search_query,
    }

    return render(request, 'home.html', context)
   
# ============================================================================
# РЕГИСТРАЦИЯ И ПОДТВЕРЖДЕНИЕ EMAIL
# ============================================================================

User = get_user_model()

def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email_confirmed = False  # Email не подтверждён при регистрации
            user.save()
            
            # Отправка письма с подтверждением
            try:
                user.send_confirmation_email(request)
                messages.success(
                    request, 
                    'Регистрация успешна! На ваш email отправлено письмо с подтверждением.'
                )
            except Exception as e:
                messages.warning(
                    request, 
                    f'Регистрация успешна, но не удалось отправить письмо: {e}. '
                    'Обратитесь к администратору.'
                )
            
            # Показываем страницу с информацией о подтверждении
            return render(request, 'accounts/email_confirmation_sent.html', {'user': user})
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form,
        'title': 'Регистрация'
    }
    return render(request, 'accounts/register.html', context)

def confirm_email(request, uidb64, token):
    """Подтверждение email"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and email_confirmation_token.check_token(user, token):
        if not user.email_confirmed:
            user.email_confirmed = True
            user.save()
            messages.success(request, 'Ваш email успешно подтверждён! Теперь вы можете войти в систему.')
        else:
            messages.info(request, 'Ваш email уже подтверждён ранее.')
        return redirect('login')
    else:
        messages.error(request, 'Ссылка для подтверждения недействительна или устарела.')
        return redirect('register')

def resend_confirmation_email(request):
    """Повторная отправка письма с подтверждением"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if not user.email_confirmed:
                user.send_confirmation_email(request)
                messages.success(request, f'Письмо с подтверждением отправлено на {email}')
            else:
                messages.info(request, 'Этот email уже подтверждён.')
        except User.DoesNotExist:
            messages.error(request, 'Пользователь с таким email не найден.')
        return redirect('login')
    
    context = {'title': 'Повторная отправка подтверждения'}
    return render(request, 'accounts/resend_confirmation.html', context)

# ============================================================================
# ВХОД В СИСТЕМУ (ИСПРАВЛЕННАЯ ВЕРСИЯ)
# ============================================================================

def custom_login(request):
    """Простая функция для входа в систему (вместо класса)"""
    print("=== DEBUG: custom_login called ==")  # Отладка
    
    # Если пользователь уже авторизован, перенаправляем на главную
    if request.user.is_authenticated:
        print("=== DEBUG: User already authenticated ==")
        return redirect('home')
    
    if request.method == 'POST':
        print("=== DEBUG: POST request received ==")
        form = CustomAuthenticationForm(request, data=request.POST)
        print(f"=== DEBUG: Form is valid: {form.is_valid()} ==")
        
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            print(f"=== DEBUG: Email: {email}, Password: {password} ==")
            
            # Аутентифицируем пользователя
            user = authenticate(request, username=email, password=password)
            print(f"=== DEBUG: Authenticated user: {user} ==")
            
            if user is not None:
                # ВРЕМЕННО: пропускаем проверку email для тестирования
                print("=== DEBUG: Logging in user ==")
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.email}!')
                return redirect('home')
            else:
                print("=== DEBUG: Authentication failed ==")
                messages.error(request, 'Неверный email или пароль.')
        else:
            print("=== DEBUG: Form errors:", form.errors)
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = CustomAuthenticationForm()
        print("=== DEBUG: GET request ==")
    
    return render(request, 'accounts/login.html', {'form': form})

# ============================================================================
# ВЫХОД ИЗ СИСТЕМЫ
# ============================================================================
def custom_logout(request):
    """Выход из системы"""
    if request.method == 'POST':
        auth_logout(request)
        messages.success(request, 'Вы успешно вышли из системы.')
        return redirect('home')
    
    # Если GET запрос, показываем страницу подтверждения
    return render(request, 'accounts/logout.html')
# ============================================================================
# ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# ============================================================================

@login_required
def profile(request):
    """Редактирование профиля пользователя"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    # Получаем заказы пользователя
    from orders.models import Order
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'form': form,
        'title': 'Мой профиль'
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def become_master(request):
    """Пользователь становится мастером"""
    if request.user.is_master():
        messages.info(request, 'Вы уже являетесь мастером')
        return redirect('master_dashboard')
    
    if request.method == 'POST':
        request.user.role = 'master'
        request.user.save()
        messages.success(request, 'Поздравляем! Теперь вы мастер!')
        return redirect('master_dashboard')
    
    return render(request, 'accounts/become_master.html')

@login_required
def master_dashboard(request):
    """Панель управления для мастера"""
    if not request.user.is_master():
        messages.error(request, 'Эта страница доступна только мастерам')
        return redirect('home')
    
    try:
        from products.models import Product
        from orders.models import Order, OrderItem
        from materials.models import Material
        from reviews.models import Review
        
        # Товары мастера
        products = Product.objects.filter(master=request.user, status='active')
        total_products = products.count()
        
        # Заказы мастера через OrderItem
        order_items = OrderItem.objects.filter(product__master=request.user)
        orders = Order.objects.filter(items__in=order_items).distinct()
        
        total_orders = orders.count()
        pending_orders = orders.filter(status='pending').count()
        
        # Выручка (сумма завершенных заказов)
        completed_orders = orders.filter(status='completed')
        total_income = sum(order.total_amount for order in completed_orders)
        
        # Материалы мастера
        materials_count = Material.objects.filter(master=request.user).count()
        
        # Отзывы на товары мастера
        reviews_count = Review.objects.filter(product__master=request.user).count()
        
        # Список заказов для отображения (если нужен)
        recent_orders = orders.order_by('-created_at')[:5]
        
    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        # Значения по умолчанию
        products = []
        total_products = 0
        total_orders = 0
        pending_orders = 0
        total_income = 0
        materials_count = 0
        reviews_count = 0
        recent_orders = []
    
    context = {
        'title': 'Панель мастера',
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_income': total_income,
        'materials_count': materials_count,
        'reviews_count': reviews_count,
        'products': products[:5],  # Последние 5 товаров
        'recent_orders': recent_orders,
    }
    return render(request, 'accounts/master_dashboard.html', context)

def master_detail(request, user_id):
    """Страница мастера для покупателей"""
    master = get_object_or_404(User, id=user_id, role='master')
    
    # Если у мастера есть товары
    try:
        products = master.products.filter(status='active')[:12]
    except:
        products = []
    
    context = {
        'master': master,
        'products': products,
        'title': f'Мастерская {master.first_name} {master.last_name}'
    }
    return render(request, 'accounts/master_detail.html', context)

def master_list(request):
    """Список всех мастеров"""
    masters = User.objects.filter(role='master').order_by('-date_joined')
    
    context = {
        'masters': masters,
        'title': 'Наши мастера'
    }
    return render(request, 'accounts/master_list.html', context)

# ============================================================================
# СМЕНА ПАРОЛЯ
# ============================================================================

@login_required
def change_password(request):
    """Смена пароля"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Обновляем сессию после смены пароля
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'title': 'Смена пароля'
    }
    return render(request, 'accounts/change_password.html', context)