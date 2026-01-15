from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Product, Category
from materials.models import Material

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
    ).exclude(technique='').values_list('technique', flat=True).distinct()
    
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