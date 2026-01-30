# test_materials_system.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masterskaya.settings')
django.setup()

from django.contrib.auth import get_user_model
from materials.models import Material, MaterialRecipe, MaterialReservation
from products.models import Product
from orders.models import Order, OrderItem
from decimal import Decimal

User = get_user_model()

print("=== ТЕСТИРОВАНИЕ СИСТЕМЫ УЧЁТА МАТЕРИАЛОВ ===")

# 1. Создаём тестового мастера
master, created = User.objects.get_or_create(
    email='test_master@example.com',
    defaults={
        'first_name': 'Тестовый',
        'last_name': 'Мастер',
        'role': 'master',
        'is_active': True
    }
)

if created:
    master.set_password('testpass123')
    master.save()
    print(f"✅ Создан мастер: {master.email}")

# 2. Создаём тестовые материалы
materials_data = [
    {
        'name': 'Тестовая шерсть',
        'current_quantity': Decimal('100.0'),
        'unit': 'm',
        'min_quantity': Decimal('10.0'),
        'price_per_unit': Decimal('150.0'),
        'color': 'Белый',
        'supplier': 'Тестовый поставщик',
    },
    {
        'name': 'Тестовая ткань',
        'current_quantity': Decimal('50.0'),
        'unit': 'm',
        'min_quantity': Decimal('5.0'),
        'price_per_unit': Decimal('80.0'),
        'color': 'Синий',
        'supplier': 'Тестовый поставщик',
    },
]

for data in materials_data:
    material, created = Material.objects.get_or_create(
        master=master,
        name=data['name'],
        defaults=data
    )
    status = "создан" if created else "уже существует"
    print(f"✅ Материал '{material.name}' {status}")

# 3. Проверяем методы материалов
wool = Material.objects.get(name='Тестовая шерсть', master=master)
print(f"\n=== ТЕСТ МЕТОДОВ МАТЕРИАЛА ===")
print(f"Материал: {wool}")
print(f"Низкий запас? {wool.is_low_stock}")
print(f"Стоимость запаса: {wool.stock_value} руб.")
print(f"Доступное количество: {wool.available_quantity}")

# 4. Проверяем создание рецепта
test_product, created = Product.objects.get_or_create(
    master=master,
    name='Тестовый свитер',
    defaults={
        'description': 'Тестовый продукт для проверки',
        'price': Decimal('2000.0'),
        'stock_quantity': 10,
        'is_active': True,
    }
)

if created:
    print(f"\n✅ Создано тестовое изделие: {test_product.name}")
    
    # Создаём рецепт
    recipe = MaterialRecipe.objects.create(
        product=test_product,
        material=wool,
        consumption_rate=Decimal('2.5'),
        waste_factor=Decimal('0.1'),
        auto_consume=True
    )
    print(f"✅ Создан рецепт: {recipe}")
    print(f"  Норма расхода: {recipe.consumption_rate} м/шт.")
    print(f"  С отходами: {recipe.calculate_required(1)} м/шт.")
    print(f"  На 5 шт. нужно: {recipe.calculate_required(5)} м")

# 5. Проверяем менеджер материалов
print("\n=== ТЕСТ МЕНЕДЖЕРА МАТЕРИАЛОВ ===")
from materials.utils import MaterialManager

report = MaterialManager.get_material_report(master.id)
print(f"Всего материалов: {report['total_materials']}")
print(f"Низкий запас: {report['low_stock']}")
print(f"Общая стоимость: {report['total_value']} руб.")

# 6. Проверяем список для заказа
reorder_list = MaterialManager.generate_reorder_list(master.id)
print(f"\n=== СПИСОК ДЛЯ ЗАКАЗА ===")
for item in reorder_list:
    print(f"{item['material_name']}: текущ. {item['current']}, мин. {item['min']}, рекоменд. {item['suggested']} {item['unit']}")

print("\n✅ Тестирование завершено успешно!")
print(f"\nДанные для входа в админку:")
print(f"Email: {master.email}")
print(f"Пароль: testpass123")