# test_connection.py
import psycopg2

try:
    # Попробуйте с этими параметрами
    conn = psycopg2.connect(
        dbname="Mastery",
        user="postgres",
        password="Onyx_2022",  # замените на ваш пароль
        host="localhost",
        port="5432"
    )
    print("✅ Подключение к PostgreSQL успешно!")
    
    cur = conn.cursor()
    
    # Проверим версию PostgreSQL
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"📦 Версия PostgreSQL: {version[0]}")
    
    # Проверим текущую базу
    cur.execute("SELECT current_database();")
    db_name = cur.fetchone()
    print(f"🗄️ Имя базы данных: {db_name[0]}")
    
    # Список всех баз
    cur.execute("SELECT datname FROM pg_database;")
    databases = cur.fetchall()
    print("📊 Все базы данных:")
    for db in databases:
        print(f"  - {db[0]}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
    print("\n🔍 Возможные причины:")
    print("1. PostgreSQL не запущен")
    print("2. Неправильный пароль")
    print("3. Базы данных Mastery не существует")
    print("4. Пользователь postgres не имеет прав")