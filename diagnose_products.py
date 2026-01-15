# diagnose_products.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masterskaya.settings')
django.setup()

print("=" * 60)
print("ДИАГНОСТИКА ПРОБЛЕМЫ С ТОВАРАМИ")
print("=" * 60)

from products.models import Product, Category
from django.core.exceptions import FieldError

# 1. Проверяем товары
print("\n1. ПРОВЕРКА ТОВАРОВ В БАЗЕ:")
try:
    all_products = Product.objects.all()
    print(f"   Всего товаров в базе: {all_products.count()}")
    
    for p in all_products:
        print(f"\n   Товар: {p.name}")
        print(f"     ID: {p.id}")
        print(f"     Статус: {p.status}")
        print(f"     Мастер: {p.master.email if p.master else 'нет'}")
        print(f"     Категория: {p.category.name if p.category else 'нет'}")
        print(f"     Цена: {p.price}")
        
except Exception as e:
    print(f"   ❌ Ошибка при получении товаров: {e}")

# 2. Проверяем активные товары
print("\n2. АКТИВНЫЕ ТОВАРЫ:")
try:
    active_products = Product.objects.filter(status='active')
    print(f"   Активных товаров: {active_products.count()}")
    
    if active_products.exists():
        print("   Список активных товаров:")
        for p in active_products:
            print(f"     - {p.name} (ID: {p.id})")
    else:
        print("   ❌ НЕТ активных товаров!")
        print("   Проверьте статусы товаров в админке")
        
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# 3. Проверяем метод get_main_image()
print("\n3. ПРОВЕРКА МЕТОДА GET_MAIN_IMAGE():")
try:
    if active_products.exists():
        product = active_products.first()
        main_image = product.get_main_image()
        if main_image:
            print(f"   ✓ Метод работает: {main_image}")
        else:
            print(f"   ⚠ У товара нет основного изображения")
            
        # Проверяем изображения
        images_count = product.images.count()
        print(f"   Изображений у товара: {images_count}")
    else:
        print("   ⚠ Нет активных товаров для проверки")
        
except Exception as e:
    print(f"   ❌ Ошибка в методе get_main_image(): {e}")

# 4. Проверяем шаблон
print("\n4. ПРОВЕРКА ШАБЛОНА:")
template_path = "templates/products/product_list.html"
if os.path.exists(template_path):
    print(f"   ✓ Шаблон найден: {template_path}")
else:
    print(f"   ❌ Шаблон не найден: {template_path}")

# 5. Тестируем view вручную
print("\n5. ТЕСТ VIEW ФУНКЦИИ:")
try:
    from django.test import RequestFactory
    from products import views
    
    # Создаем тестовый запрос
    factory = RequestFactory()
    request = factory.get('/products/')
    
    # Добавляем user в запрос (если нужно)
    request.user = None
    
    # Вызываем view
    response = views.product_list(request)
    
    print(f"   ✓ View функция работает")
    print(f"   Статус ответа: {response.status_code}")
    
    # Проверяем контекст
    if hasattr(response, 'context_data'):
        products_in_context = response.context_data.get('products', [])
        print(f"   Товаров в контексте: {len(products_in_context)}")
        
except Exception as e:
    print(f"   ❌ Ошибка в view: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("ВЫВОДЫ:")
print("=" * 60)

if active_products.exists():
    print("✅ Есть активные товары в базе")
    print("⚠ Проблема в отображении (шаблон или контекст)")
else:
    print("❌ НЕТ активных товаров!")
    print("👉 Перейдите в админку и измените статус товаров на 'active'")

print("\n" + "=" * 60)