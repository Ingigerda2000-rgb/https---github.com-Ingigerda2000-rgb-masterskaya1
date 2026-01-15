# create_test_data.py
import os
import django
import sys

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masterskaya.settings')
django.setup()

from products.models import Category, Product
from materials.models import Material, MaterialRecipe
from accounts.models import User
from django.db import transaction

@transaction.atomic
def create_test_data():
    print("=" * 60)
    print("СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ МАГАЗИНА РУКОДЕЛЬНЫХ ИЗДЕЛИЙ")
    print("=" * 60)
    
    # Создаем мастера (без username)
    print("\n1. Создание пользователей...")
    master, created = User.objects.get_or_create(
        email='master@example.com',
        defaults={
            'role': 'master',
            'first_name': 'Мария',
            'last_name': 'Творческая',
            'is_active': True,
            'is_staff': True  # Для доступа в админку
        }
    )
    if created:
        master.set_password('master123')
        master.save()
        print(f"   ✓ Создан мастер: {master.get_full_name()} ({master.email})")
    else:
        print(f"   → Мастер уже существует: {master.email}")
    
    # Создаем покупателя (без username)
    buyer, created = User.objects.get_or_create(
        email='buyer@example.com',
        defaults={
            'role': 'buyer',
            'first_name': 'Иван',
            'last_name': 'Покупатель',
            'is_active': True
        }
    )
    if created:
        buyer.set_password('buyer123')
        buyer.save()
        print(f"   ✓ Создан покупатель: {buyer.get_full_name()} ({buyer.email})")
    else:
        print(f"   → Покупатель уже существует: {buyer.email}")
    
    # Создаем администратора
    admin, created = User.objects.get_or_create(
        email='admin@example.com',
        defaults={
            'role': 'admin',
            'first_name': 'Администратор',
            'last_name': 'Системы',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin.set_password('admin123')
        admin.save()
        print(f"   ✓ Создан администратор: {admin.get_full_name()} ({admin.email})")
    else:
        print(f"   → Администратор уже существует: {admin.email}")
    
    # Создаем категории
    print("\n2. Создание категорий...")
    categories_data = [
        {'name': 'Вязаные изделия', 'description': 'Теплые и уютные вязаные вещи'},
        {'name': 'Головные уборы', 'description': 'Шапки, шарфы, береты'},
        {'name': 'Украшения и аксессуары', 'description': 'Бижутерия, сумки, пояса'},
        {'name': 'Декор для дома', 'description': 'Интерьерные изделия ручной работы'},
        {'name': 'Куклы и игрушки', 'description': 'Игрушки и куклы любимых персонажей'},
    ]
    
    categories = {}
    categories_created = 0
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        categories[cat_data['name']] = category
        if created:
            categories_created += 1
            print(f"   ✓ Категория: {category.name}")
    
    print(f"   → Создано категорий: {categories_created}/{len(categories_data)}")
    
    # Создаем материалы
    print("\n3. Создание материалов...")
    materials_data = [
        {'name': 'Шерсть мериноса', 'unit': 'g', 'current_quantity': 5000, 
         'price_per_unit': 0.5, 'color': 'белый', 'texture': 'мягкая'},
        {'name': 'Акриловая пряжа', 'unit': 'g', 'current_quantity': 3000, 
         'price_per_unit': 0.3, 'color': 'разноцветная', 'texture': 'гладкая'},
        {'name': 'Хлопковая нить', 'unit': 'm', 'current_quantity': 1000, 
         'price_per_unit': 2.0, 'color': 'бежевый', 'texture': 'тонкая'},
        {'name': 'Льняная ткань', 'unit': 'm', 'current_quantity': 50, 
         'price_per_unit': 15.0, 'color': 'натуральный', 'texture': 'грубая'},
        {'name': 'Фетр', 'unit': 'pcs', 'current_quantity': 20, 
         'price_per_unit': 25.0, 'color': 'разные цвета', 'texture': 'плотный'},
        {'name': 'Бисер', 'unit': 'g', 'current_quantity': 1000, 
         'price_per_unit': 0.1, 'color': 'разноцветный', 'texture': 'мелкий'},
    ]
    
    materials = {}
    materials_created = 0
    for mat_data in materials_data:
        material, created = Material.objects.get_or_create(
            name=mat_data['name'],
            master=master,
            defaults={
                'unit': mat_data['unit'],
                'current_quantity': mat_data['current_quantity'],
                'min_quantity': 100,
                'price_per_unit': mat_data['price_per_unit'],
                'color': mat_data['color'],
                'texture': mat_data['texture'],
            }
        )
        materials[mat_data['name']] = material
        if created:
            materials_created += 1
            print(f"   ✓ Материал: {material.name} - {material.current_quantity} {material.get_unit_display()}")
    
    print(f"   → Создано материалов: {materials_created}/{len(materials_data)}")
    
    # Создаем товары
    print("\n4. Создание товаров...")
    products_data = [
        {
            'name': 'Вязаная шапка из шерсти мериноса',
            'description': 'Теплая зимняя шапка ручной вязки из натуральной шерсти мериноса. Идеальна для холодной погоды.',
            'price': 2500,
            'category': categories['Головные уборы'],
            'stock_quantity': 10,
            'technique': 'вязание спицами',
            'difficulty_level': 'intermediate',
            'production_time_days': 3,
            'color': 'серый',
            'materials_recipes': [
                {'material': 'Шерсть мериноса', 'consumption': 200, 'waste': 0.1},
            ]
        },
        {
            'name': 'Вязаный свитер',
            'description': 'Мягкий и теплый свитер из акриловой пряжи. Безопасный гипоаллергенный материал.',
            'price': 3500,
            'category': categories['Вязаные изделия'],
            'stock_quantity': 5,
            'technique': 'вязание крючком',
            'difficulty_level': 'advanced',
            'production_time_days': 5,
            'color': 'голубой',
            'materials_recipes': [
                {'material': 'Акриловая пряжа', 'consumption': 600, 'waste': 0.45},
            ]
        },
        {
            'name': 'Вязаный шарф с узором',
            'description': 'Длинный шарф с ажурным узором. Прекрасно сочетается с пальто и куртками.',
            'price': 1800,
            'category': categories['Головные уборы'],
            'stock_quantity': 8,
            'technique': 'вязание спицами',
            'difficulty_level': 'beginner',
            'production_time_days': 2,
            'color': 'бордовый',
            'materials_recipes': [
                {'material': 'Шерсть мериноса', 'consumption': 150, 'waste': 0.1},
                {'material': 'Акриловая пряжа', 'consumption': 50, 'waste': 0.1},
            ]
        },
        {
            'name': 'Льняная салфетка с вышивкой',
            'description': 'Элегантная салфетка из натурального льна с ручной вышивкой. Украсит любой стол.',
            'price': 1200,
            'category': categories['Декор для дома'],
            'stock_quantity': 15,
            'technique': 'вышивка',
            'difficulty_level': 'intermediate',
            'production_time_days': 4,
            'color': 'белый',
            'materials_recipes': [
                {'material': 'Льняная ткань', 'consumption': 0.5, 'waste': 0.2},
                {'material': 'Хлопковая нить', 'consumption': 2, 'waste': 0.1},
            ]
        },
        {
            'name': 'Фетровая брошь-цветок',
            'description': 'Нежная брошь из фетра в виде цветка. Отлично подойдет к пальто или кардигану.',
            'price': 800,
            'category': categories['Украшения и аксессуары'],
            'stock_quantity': 20,
            'technique': 'работа с фетром',
            'difficulty_level': 'beginner',
            'production_time_days': 1,
            'color': 'розовый',
            'materials_recipes': [
                {'material': 'Фетр', 'consumption': 0.2, 'waste': 0.05},
                {'material': 'Бисер', 'consumption': 10, 'waste': 0.02},
            ]
        },
    ]
    
    products_created = 0
    recipes_created = 0
    
    for prod_data in products_data:
    # Сначала создаем товар без сохранения в базе
     product, created = Product.objects.get_or_create(
        name=prod_data['name'],
        master=master,
        defaults={
            'description': prod_data['description'],
            'price': prod_data['price'],
            'category': prod_data['category'],
            'stock_quantity': prod_data['stock_quantity'],
            'status': 'active',
            'technique': prod_data['technique'],
            'difficulty_level': prod_data['difficulty_level'],
            'production_time_days': prod_data['production_time_days'],
            'color': prod_data['color'],
        }
    )
    
    if created:
        products_created += 1
        
        # Сначала сохраняем товар
        product.save()
        
        # Теперь создаем рецепты материалов
        for recipe_data in prod_data['materials_recipes']:
            material = materials[recipe_data['material']]
            recipe, recipe_created = MaterialRecipe.objects.get_or_create(
                product=product,
                material=material,
                defaults={
                    'consumption_rate': recipe_data['consumption'],
                    'waste_factor': recipe_data['waste']
                }
            )
            if recipe_created:
                recipes_created += 1
            
            # Добавляем материал к товару
            product.materials.add(material)
            
            # Рассчитываем базовую стоимость материалов
            material_cost = product.calculate_material_cost()
            product.base_cost = material_cost
            product.save()
            
            print(f"   ✓ Товар: {product.name}")
            print(f"     Цена: {product.price} руб.")
            print(f"     Материалы: {material_cost:.2f} руб.")
            print(f"     Маржа: {product.price - material_cost:.2f} руб.")
    
    print(f"   → Создано товаров: {products_created}/{len(products_data)}")
    print(f"   → Создано рецептов: {recipes_created}")
    
    print("\n" + "=" * 60)
    print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    print("=" * 60)
    print(f"• Пользователей: {User.objects.count()}")
    print(f"• Категорий: {Category.objects.count()}")
    print(f"• Материалов: {Material.objects.count()}")
    print(f"• Товаров: {Product.objects.count()} (создано: {products_created})")
    print(f"• Рецептов материалов: {MaterialRecipe.objects.count()}")
    print("\nДанные для входа:")
    print("Мастер: email: master@example.com, пароль: master123")
    print("Покупатель: email: buyer@example.com, пароль: buyer123")
    print("Администратор: email: admin@example.com, пароль: admin123")
    print("\nТестовые данные успешно созданы!")
    print("=" * 60)

if __name__ == '__main__':
    try:
        create_test_data()
    except Exception as e:
        print(f"\n❌ Ошибка при создании тестовых данных: {e}")
        print("\nВозможные причины и решения:")
        print("1. Проверьте, применены ли миграции:")
        print("   python manage.py makemigrations")
        print("   python manage.py migrate")
        print("\n2. Проверьте, нет ли циклических импортов в моделях")
        print("\n3. Проверьте корректность полей в моделях User, Product, Material")
        
        # Более подробная информация об ошибке
        import traceback
        print("\nПодробный traceback:")
        traceback.print_exc()