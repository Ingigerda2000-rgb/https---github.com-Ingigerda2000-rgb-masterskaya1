# check_products.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masterskaya.settings')
django.setup()

from products.models import Product, Category

print("=" * 60)
print("ПРОВЕРКА ТОВАРОВ И КАТЕГОРИЙ")
print("=" * 60)

# Все товары
print("\n1. ВСЕ ТОВАРЫ:")
products = Product.objects.all()
for p in products:
    print(f"  ID: {p.id}, Название: {p.name}")
    print(f"    Статус: {p.status}, Цена: {p.price} руб.")
    print(f"    Категория: {p.category.name if p.category else 'нет'}")
    print(f"    Мастер: {p.master.email}")
    print()

# Активные товары
print("\n2. АКТИВНЫЕ ТОВАРЫ:")
active_products = Product.objects.filter(status='active')
print(f"  Всего активных: {active_products.count()}")
for p in active_products:
    print(f"  - {p.name}")

# Категории
print("\n3. КАТЕГОРИИ:")
categories = Category.objects.all()
for cat in categories:
    product_count = cat.products.count()
    print(f"  - {cat.name}: {product_count} товаров")

print("\n" + "=" * 60)
print("РЕКОМЕНДАЦИИ:")
print("=" * 60)
if active_products.count() == 0:
    print("❌ Нет активных товаров!")
    print("   В админке измените статус товаров на 'Активен'")
else:
    print(f"✅ Есть {active_products.count()} активных товаров")
    print("   Проверьте views.py и шаблоны")