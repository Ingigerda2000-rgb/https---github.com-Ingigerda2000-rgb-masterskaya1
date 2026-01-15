# test_simple.py
import os
import django
import sys

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masterskaya.settings')
django.setup()

from accounts.models import User

print("=" * 50)
print("ПРОСТОЙ ТЕСТ СИСТЕМЫ")
print("=" * 50)

try:
    # 1. Проверяем модель User
    print("1. Проверка модели User...")
    
    # Считаем пользователей
    user_count = User.objects.count()
    print(f"   В базе пользователей: {user_count}")
    
    # 2. Создаем тестового пользователя
    print("\n2. Создание тестового пользователя...")
    
    # Удаляем если уже есть
    User.objects.filter(email='test_simple@test.com').delete()
    
    # Создаем нового
    user = User.objects.create(
        email='test_simple@test.com',
        role='buyer',
        first_name='Тестовый',
        last_name='Пользователь',
        is_active=True
    )
    user.set_password('test123')
    user.save()
    
    print(f"   ✓ Создан: {user.email}")
    print(f"   Роль: {user.get_role_display()}")
    
    # 3. Проверяем что сохранился
    print("\n3. Проверка сохранения...")
    saved_user = User.objects.get(email='test_simple@test.com')
    print(f"   ✓ Найден в базе: {saved_user.get_full_name()}")
    
    # 4. Проверка пароля
    print("\n4. Проверка пароля...")
    if saved_user.check_password('test123'):
        print("   ✓ Пароль работает корректно")
    else:
        print("   ✗ Пароль не работает")
    
    print("\n" + "=" * 50)
    print("ТЕСТ ПРОЙДЕН УСПЕШНО!")
    print("=" * 50)
    
except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    print("\nВозможные причины:")
    print("1. Не выполнены миграции")
    print("2. Ошибка в модели User")
    print("3. Проблемы с настройками Django")
    
    import traceback
    traceback.print_exc()