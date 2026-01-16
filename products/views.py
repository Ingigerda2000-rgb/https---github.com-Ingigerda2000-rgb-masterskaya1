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
    product = get_object_or_404(Product, id=product_id, status='active')
    
    # Получаем похожие товары
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
