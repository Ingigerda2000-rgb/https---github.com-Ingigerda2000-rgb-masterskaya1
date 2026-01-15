# fix_m2m_table.py
import os
import django
from django.db import connection, transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masterskaya.settings')
django.setup()

print("=" * 60)
print("ИСПРАВЛЕНИЕ ТАБЛИЦЫ M2M СВЯЗЕЙ")
print("=" * 60)

with transaction.atomic():
    with connection.cursor() as cursor:
        # 1. Проверяем существует ли таблица
        if connection.vendor == 'postgresql':
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'products_product_materials'
                )
            """)
            exists = cursor.fetchone()[0]
        else:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='products_product_materials'
            """)
            exists = cursor.fetchone() is not None
        
        if exists:
            print("✅ Таблица уже существует")
        else:
            print("🔄 Создаем таблицу products_product_materials...")
            
            if connection.vendor == 'postgresql':
                # Для PostgreSQL
                cursor.execute("""
                    CREATE TABLE products_product_materials (
                        id SERIAL PRIMARY KEY,
                        product_id INTEGER NOT NULL REFERENCES products_product(id) DEFERRABLE INITIALLY DEFERRED,
                        material_id INTEGER NOT NULL REFERENCES materials_material(id) DEFERRABLE INITIALLY DEFERRED,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(product_id, material_id)
                    )
                """)
                
                # Создаем индексы
                cursor.execute("""
                    CREATE INDEX products_product_materials_product_id_idx 
                    ON products_product_materials(product_id)
                """)
                cursor.execute("""
                    CREATE INDEX products_product_materials_material_id_idx 
                    ON products_product_materials(material_id)
                """)
            else:
                # Для SQLite
                cursor.execute("""
                    CREATE TABLE products_product_materials (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL REFERENCES products_product(id),
                        material_id INTEGER NOT NULL REFERENCES materials_material(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(product_id, material_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX products_product_materials_product_id 
                    ON products_product_materials(product_id)
                """)
                cursor.execute("""
                    CREATE INDEX products_product_materials_material_id 
                    ON products_product_materials(material_id)
                """)
            
            print("✅ Таблица создана")
        
        # 2. Добавляем запись в django_migrations
        print("\n🔄 Добавляем запись в миграции...")
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('products', '0003_product_materials_m2m', CURRENT_TIMESTAMP)
            ON CONFLICT DO NOTHING
        """)
        
        print("✅ Запись добавлена")

print("\n" + "=" * 60)
print("ГОТОВО! ✅")
print("=" * 60)