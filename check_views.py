# check_views.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masterskaya.settings')
django.setup()

print("=" * 60)
print("ПРОВЕРКА VIEWS.PROD")
print("=" * 60)

# Импортируем views
try:
    from products import views
    print("✅ products/views.py импортируется")
    
    # Проверяем функции
    if hasattr(views, 'product_list'):
        print("✅ Есть функция product_list")
    else:
        print("❌ НЕТ функции product_list")
        
    if hasattr(views, 'product_detail'):
        print("✅ Есть функция product_detail")
    else:
        print("❌ НЕТ функции product_detail")
        
except Exception as e:
    print(f"❌ Ошибка импорта views: {e}")

# Проверяем URLs
print("\nПРОВЕРКА URLs:")
try:
    from django.urls import reverse, NoReverseMatch
    
    try:
        reverse('product_list')
        print("✅ URL 'product_list' работает")
    except NoReverseMatch:
        print("❌ URL 'product_list' не найден")
        
    try:
        reverse('product_detail', args=[1])
        print("✅ URL 'product_detail' работает")
    except NoReverseMatch:
        print("❌ URL 'product_detail' не найден")
        
except Exception as e:
    print(f"❌ Ошибка проверки URLs: {e}")

print("\n" + "=" * 60)