# add_materials.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masterskaya.settings')
django.setup()

from accounts.models import User
from products.models import Product, Category
from materials.models import Material, MaterialRecipe

print("=" * 60)
print("ДОБАВЛЕНИЕ МАТЕРИАЛОВ И СВЯЗЕЙ")
print("=" * 60)

# 1. Находим мастера
try:
    master = User.objects.filter(role='master').first()
    if not master:
        print("❌ Не найден мастер")
        # Создаем мастера если нет
        master = User.objects.create(
            email='master_real@test.com',
            role='master',
            first_name='Реальный',
            last_name='Мастер',
            is_active=True
        )
        master.set_password('master123')
        master.save()
        print(f"✓ Создан мастер: {master.email}")
    else:
        print(f"✓ Найден мастер: {master.email}")
except Exception as e:
    print(f"❌ Ошибка поиска мастера: {e}")
    exit()

# 2. Создаем материалы
print("\n2. Создание материалов...")
materials_data = [
    {'name': 'Шерсть', 'unit': 'g', 'quantity': 5000, 'price': 0.5},
    {'name': 'Пряжа', 'unit': 'g', 'quantity': 3000, 'price': 0.3},
    {'name': 'Нить', 'unit': 'm', 'quantity': 1000, 'price': 2.0},
]

materials = {}
for mat in materials_data:
    material, created = Material.objects.get_or_create(
        name=mat['name'],
        master=master,
        defaults={
            'unit': mat['unit'],
            'current_quantity': mat['quantity'],
            'min_quantity': 100,
            'price_per_unit': mat['price'],
            'color': 'разные'
        }
    )
    materials[mat['name']] = material
    if created:
        print(f"  ✓ Материал: {material.name}")
    else:
        print(f"  → Материал уже есть: {material.name}")

# 3. Добавляем материалы к товарам
print("\n3. Добавление материалов к товарам...")

products = Product.objects.all()
for product in products:
    print(f"\n  Товар: {product.name}")
    
    # Очищаем старые связи (если есть)
    product.materials.clear()
    
    # Добавляем материалы в зависимости от названия товара
    if 'шапка' in product.name.lower():
        product.materials.add(materials['Шерсть'])
        print(f"    ✓ Добавлена шерсть")
        
        # Создаем рецепт
        MaterialRecipe.objects.get_or_create(
            product=product,
            material=materials['Шерсть'],
            defaults={'consumption_rate': 200, 'waste_factor': 0.1}
        )
        
    elif 'шарф' in product.name.lower():
        product.materials.add(materials['Пряжа'])
        print(f"    ✓ Добавлена пряжа")
        
        MaterialRecipe.objects.get_or_create(
            product=product,
            material=materials['Пряжа'],
            defaults={'consumption_rate': 150, 'waste_factor': 0.1}
        )
        
    else:
        # Для остальных товаров добавляем оба материала
        product.materials.add(materials['Шерсть'], materials['Пряжа'])
        print(f"    ✓ Добавлены шерсть и пряжа")
        
        for material in [materials['Шерсть'], materials['Пряжа']]:
            MaterialRecipe.objects.get_or_create(
                product=product,
                material=material,
                defaults={'consumption_rate': 100, 'waste_factor': 0.1}
            )

print("\n" + "=" * 60)
print("ГОТОВО! ✅")
print("=" * 60)
print(f"• Материалов: {Material.objects.count()}")
print(f"• Рецептов: {MaterialRecipe.objects.count()}")

# 4. Проверяем связи
print("\n4. Проверка связей...")
for product in Product.objects.all():
    mat_count = product.materials.count()
    print(f"  {product.name}: {mat_count} материалов")
    
print("\n🌐 Запустите сервер: python manage.py runserver")