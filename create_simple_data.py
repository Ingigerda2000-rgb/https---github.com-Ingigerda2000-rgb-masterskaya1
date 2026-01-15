# create_simple_data.py
import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masterskaya.settings')
django.setup()

from accounts.models import User
from products.models import Category, Product
from django.db import transaction, connection

@transaction.atomic
def create_simple_data():
    print("=" * 60)
    print("СОЗДАНИЕ ПРОСТЫХ ДАННЫХ")
    print("=" * 60)
    
    # 1. Очищаем старые данные (АККУРАТНО)
    print("\n1. Очистка старых данных...")
    
    try:
        # Сначала удаляем продукты
        Product.objects.all().delete()
        print("   ✓ Товары удалены")
    except Exception as e:
        print(f"   ⚠ Не удалось удалить товары: {e}")
        # Пропускаем ошибку, продолжаем
    
    try:
        # Удаляем категории
        Category.objects.all().delete()
        print("   ✓ Категории удалены")
    except Exception as e:
        print(f"   ⚠ Не удалось удалить категории: {e}")
    
    # Удаляем тестовых пользователей
    test_emails = ['master@test.com', 'buyer@test.com', 'admin@test.com']
    User.objects.filter(email__in=test_emails).delete()
    print("   ✓ Тестовые пользователи удалены")
    
    # 2. Создаем пользователей
    print("\n2. Создание пользователей...")
    
    try:
        # Мастер
        master = User.objects.create(
            email='master@test.com',
            role='master',
            first_name='Мария',
            last_name='Мастерова',
            is_active=True
        )
        master.set_password('master123')
        master.save()
        print(f"   ✓ Мастер создан: {master.email}")
        
        # Покупатель
        buyer = User.objects.create(
            email='buyer@test.com',
            role='buyer',
            first_name='Иван',
            last_name='Покупателев',
            is_active=True
        )
        buyer.set_password('buyer123')
        buyer.save()
        print(f"   ✓ Покупатель создан: {buyer.email}")
        
        # Админ
        admin = User.objects.create(
            email='admin@test.com',
            role='admin',
            first_name='Админ',
            last_name='Админов',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        admin.set_password('admin123')
        admin.save()
        print(f"   ✓ Админ создан: {admin.email}")
        
    except Exception as e:
        print(f"   ✗ Ошибка создания пользователей: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Создаем категории
    print("\n3. Создание категорий...")
    
    try:
        categories_data = [
            'Вязаные изделия',
            'Головные уборы', 
            'Аксессуары',
        ]
        
        categories = {}
        for name in categories_data:
            category = Category.objects.create(name=name)
            categories[name] = category
            print(f"   ✓ Категория: {name}")
            
    except Exception as e:
        print(f"   ✗ Ошибка создания категорий: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Создаем товары (БЕЗ связей с материалами)
    print("\n4. Создание товаров...")
    
    try:
        products_data = [
            {
                'name': 'Вязаная шапка',
                'description': 'Теплая зимняя шапка ручной работы из шерсти.',
                'price': 2500,
                'category': categories['Головные уборы'],
                'technique': 'вязание спицами',
                'stock': 10
            },
            {
                'name': 'Шерстяной шарф', 
                'description': 'Длинный теплый шарф, идеальный для холодной погоды.',
                'price': 1800,
                'category': categories['Аксессуары'],
                'technique': 'вязание спицами',
                'stock': 8
            },
            {
                'name': 'Детский свитер',
                'description': 'Мягкий и теплый свитер для ребенка.',
                'price': 3500,
                'category': categories['Вязаные изделия'],
                'technique': 'вязание крючком',
                'stock': 5
            },
        ]
        
        for prod in products_data:
            product = Product.objects.create(
                name=prod['name'],
                description=prod['description'],
                price=prod['price'],
                master=master,
                category=prod['category'],
                stock_quantity=prod['stock'],
                status='active',
                technique=prod['technique'],
                difficulty_level='intermediate',
                production_time_days=3,
                color='разные'
            )
            print(f"   ✓ Товар: {product.name} - {product.price} руб.")
            
    except Exception as e:
        print(f"   ✗ Ошибка создания товаров: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("ДАННЫЕ УСПЕШНО СОЗДАНЫ! ✅")
    print("=" * 60)
    print(f"• Пользователей: {User.objects.count()}")
    print(f"• Категорий: {Category.objects.count()}")
    print(f"• Товаров: {Product.objects.count()}")
    
    print("\n👤 ДЛЯ ВХОДА:")
    print("Админка: admin@test.com / admin123")
    print("Мастер: master@test.com / master123")
    print("Покупатель: buyer@test.com / buyer123")
    
    print("\n🌐 ССЫЛКИ ДЛЯ ПРОВЕРКИ:")
    print("1. Админка: http://localhost:8000/admin/")
    print("2. Каталог товаров: http://localhost:8000/products/")
    print("=" * 60)

if __name__ == '__main__':
    try:
        create_simple_data()
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()