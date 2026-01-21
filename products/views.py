from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .models import Product, Category, ProductImage
from materials.models import Material
from .forms import ProductForm

def product_list(request):
    """Список товаров с поиском и фильтрацией"""
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
    techniques = Product.objects.filter(
        status='active',
        technique__isnull=False
    ).exclude(technique='').order_by('technique').values_list('technique', flat=True).distinct()
    
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
    ).exclude(technique='').values('technique').distinct().order_by('technique').values_list('technique', flat=True)
    
    context = {
        'products': products_page,
        'categories': categories,
        'techniques': techniques,
        'search_query': search_query,
    }
    
    return render(request, 'products/product_list.html', context)

def product_detail(request, product_id):
    """Детальная страница товара"""
    product = get_object_or_404(Product, id=product_id)

    # Проверяем доступ: активные товары для всех, неактивные только для мастера-владельца
    if product.status != 'active' and not (request.user.is_authenticated and request.user == product.master):
        from django.http import Http404
        raise Http404

    # Получаем похожие товары (только активные)
    similar_products = Product.objects.filter(
        Q(category=product.category) |
        Q(technique=product.technique)
    ).exclude(id=product.id).filter(status='active')[:4]

    # Получаем изображения
    images = product.images.all()

    context = {
        'product': product,
        'similar_products': similar_products,
        'images': images,
        'main_image': product.get_main_image(),
        'search_query': '',
    }

    return render(request, 'products/product_detail.html', context)

def master_check(user):
    """Проверка, что пользователь является мастером"""
    return user.is_authenticated and user.role == 'master'

@login_required
@user_passes_test(master_check)
def add_product(request):
    """Добавление нового товара мастером"""
    if request.method == 'POST':
        print(f"DEBUG: POST request received")
        print(f"DEBUG: FILES keys: {list(request.FILES.keys())}")
        print(f"DEBUG: FILES: {request.FILES}")

        form = ProductForm(request.POST, master=request.user)
        if form.is_valid():
            product = form.save()

            # Обработка загруженных изображений
            images = request.FILES.getlist('images')
            print(f"DEBUG: Images found: {len(images)}")
            for i, image_file in enumerate(images):
                print(f"DEBUG: Processing image {i+1}: {image_file.name}")
                ProductImage.objects.create(
                    product=product,
                    image=image_file,
                    is_main=(i == 0),  # Первое изображение делаем основным
                    order=i
                )

            messages.success(request, f'Товар "{product.name}" успешно добавлен!')
            return redirect('master_dashboard')
    else:
        form = ProductForm(master=request.user)

    context = {
        'form': form,
        'title': 'Добавить товар'
    }

    return render(request, 'products/add_product.html', context)

@login_required
@user_passes_test(master_check)
def update_product(request, product_id):
    """Редактирование товара мастером"""
    product = get_object_or_404(Product, id=product_id, master=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product, master=request.user)
        if form.is_valid():
            product = form.save()

            # Обработка новых загруженных изображений
            images = request.FILES.getlist('images')
            if images:
                # Если загружены новые изображения, удаляем старые и добавляем новые
                product.images.all().delete()  # Удаляем старые изображения
                for i, image_file in enumerate(images):
                    ProductImage.objects.create(
                        product=product,
                        image=image_file,
                        is_main=(i == 0),  # Первое изображение делаем основным
                        order=i
                    )

            messages.success(request, f'Товар "{product.name}" успешно обновлен!')
            return redirect('master_dashboard')
    else:
        form = ProductForm(instance=product, master=request.user)

    context = {
        'form': form,
        'product': product,
        'title': 'Редактировать товар'
    }

    return render(request, 'products/edit_product.html', context)

def toggle_favorite(request, product_id):
    """Добавление/удаление товара из избранного"""
    if not request.user.is_authenticated:
        # Для неавторизованных пользователей возвращаем JSON с ошибкой
        return JsonResponse({
            'success': False,
            'message': 'Необходимо войти в систему',
            'redirect': '/accounts/login/'
        })
    
    product = get_object_or_404(Product, id=product_id)
    
    # Проверяем, есть ли товар в избранном
    from .models import Favorite
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    # Если товар уже был в избранном, удаляем его
    if not created:
        favorite.delete()
        is_favorite = False
        message = 'Товар удален из избранного'
    else:
        is_favorite = True
        message = 'Товар добавлен в избранное'
    
    # Возвращаем JSON с результатом
    return JsonResponse({
        'success': True,
        'is_favorite': is_favorite,
        'message': message
    })

def check_favorite(request, product_id):
    """Проверка, находится ли товар в избранном у пользователя"""
    if not request.user.is_authenticated:
        return JsonResponse({'is_favorite': False})
    
    from .models import Favorite
    is_favorite = Favorite.objects.filter(
        user=request.user,
        product_id=product_id
    ).exists()
    
    return JsonResponse({'is_favorite': is_favorite})

@login_required
@user_passes_test(master_check)
def master_products_list(request):
    """Список товаров мастера"""
    products = Product.objects.filter(master=request.user).order_by('-created_at')

    # Пагинация
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 12)  # 12 товаров на странице

    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    context = {
        'products': products_page,
        'title': 'Мои товары'
    }

    return render(request, 'products/master_products_list.html', context)

@login_required
def favorites_list(request):
    """Список избранных товаров пользователя"""
    from .models import Favorite
    favorites = Favorite.objects.filter(user=request.user).select_related('product')

    context = {
        'favorites': favorites,
    }

    return render(request, 'products/favorites.html', context)
