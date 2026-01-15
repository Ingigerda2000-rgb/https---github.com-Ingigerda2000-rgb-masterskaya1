# quick_check.py
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masterskaya.settings')
django.setup()

print("=" * 60)
print("ПРОВЕРКА СОСТОЯНИЯ ПРОЕКТА")
print("=" * 60)

# 1. Проверка базы данных
from django.db import connection

try:
    # Пытаемся выполнить простой запрос
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
    
    print("✅ База данных подключена")
    
    # Таблицы
    tables = connection.introspection.table_names()
    print(f"📊 Таблиц в базе: {len(tables)}")
    
    if tables:
        print("\nСписок таблиц:")
        for i, table in enumerate(sorted(tables), 1):
            print(f"  {i:2}. {table}")
    
except Exception as e:
    print(f"❌ Ошибка подключения к базе: {e}")

# 2. Проверка моделей
print("\n" + "=" * 60)
print("ПРОВЕРКА МОДЕЛЕЙ")
print("=" * 60)

models_to_check = [
    ('accounts', 'User'),
    ('products', 'Product'),
    ('products', 'Category'),
    ('materials', 'Material'),
]

for app, model_name in models_to_check:
    try:
        # Динамический импорт
        module = __import__(f'{app}.models', fromlist=[model_name])
        model = getattr(module, model_name)
        count = model.objects.count()
        print(f"✅ {app}.{model_name}: {count} записей")
    except Exception as e:
        print(f"❌ {app}.{model_name}: {e}")

# 3. Проверка миграций
print("\n" + "=" * 60)
print("ПРОВЕРКА МИГРАЦИЙ")
print("=" * 60)

try:
    from django.db.migrations.loader import MigrationLoader
    loader = MigrationLoader(connection)
    
    for app_label in loader.migrated_apps:
        app_migrations = loader.graph.nodes.keys()
        app_migrations = [m for m in app_migrations if m[0] == app_label]
        
        if app_migrations:
            applied = [m for m in app_migrations if m in loader.applied_migrations]
            print(f"📦 {app_label}: {len(applied)}/{len(app_migrations)} применено")
            
except Exception as e:
    print(f"⚠ Не удалось проверить миграции: {e}")

print("\n" + "=" * 60)
print("РЕКОМЕНДАЦИИ:")
print("=" * 60)

if not tables:
    print("1. ❗ База данных пуста. Выполните:")
    print("   python manage.py migrate")
elif 'products_product' not in tables:
    print("2. ❗ Таблица товаров не создана. Выполните:")
    print("   python manage.py makemigrations")
    print("   python manage.py migrate products")
else:
    print("✅ База данных в порядке")
    print("🌐 Запустите сервер: python manage.py runserver")