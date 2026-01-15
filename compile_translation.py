import os
import struct
from pathlib import Path

def create_mo_file(po_file_path, mo_file_path):
    """
    Создает простой .mo файл из .po файла
    Это упрощенная версия, которая работает для базовых переводов
    """
    # Читаем .po файл
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Парсим переводы (упрощенно)
    translations = {}
    lines = content.split('\n')
    
    msgid = None
    msgstr = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('msgid "'):
            msgid = line[7:-1]  # Убираем msgid " и "
        elif line.startswith('msgstr "'):
            msgstr = line[8:-1]  # Убираем msgstr " и "
            if msgid and msgstr:
                translations[msgid] = msgstr
                msgid = None
                msgstr = None
    
    # Создаем .mo файл (упрощенный формат)
    with open(mo_file_path, 'wb') as f:
        # Магическое число для .mo файлов
        f.write(struct.pack('<I', 0x950412de))
        
        # Версия
        f.write(struct.pack('<I', 0))
        
        # Количество строк
        f.write(struct.pack('<I', len(translations)))
        
        # Смещение таблицы оригиналов
        f.write(struct.pack('<I', 28))
        
        # Смещение таблицы переводов
        f.write(struct.pack('<I', 28 + 8 * len(translations)))
        
        # Размер хэш-таблицы (0 для простоты)
        f.write(struct.pack('<I', 0))
        
        # Смещение хэш-таблицы
        f.write(struct.pack('<I', 0))
        
        # Записываем оригиналы и переводы
        originals = []
        translations_list = []
        
        for original, translation in translations.items():
            originals.append(original.encode('utf-8') + b'\x00')
            translations_list.append(translation.encode('utf-8') + b'\x00')
        
        # Таблица оригиналов
        offset = 28 + 16 * len(translations)
        for original in originals:
            f.write(struct.pack('<I', len(original) - 1))  # Длина без нуля
            f.write(struct.pack('<I', offset))
            offset += len(original)
        
        # Таблица переводов
        for translation in translations_list:
            f.write(struct.pack('<I', len(translation) - 1))  # Длина без нуля
            f.write(struct.pack('<I', offset))
            offset += len(translation)
        
        # Данные
        for original in originals:
            f.write(original)
        for translation in translations_list:
            f.write(translation)
    
    print(f"Создан файл: {mo_file_path}")

# Основная часть
if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent
    PO_FILE = BASE_DIR / "locale" / "ru" / "LC_MESSAGES" / "django.po"
    MO_FILE = BASE_DIR / "locale" / "ru" / "LC_MESSAGES" / "django.mo"
    
    # Создаем папки если их нет
    PO_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Если .po файла нет, создаем минимальный
    if not PO_FILE.exists():
        print(f"Создаю минимальный {PO_FILE}...")
        PO_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        minimal_po = '''# Minimal Django translations
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Username"
msgstr "Имя пользователя"

msgid "Password"
msgstr "Пароль"

msgid "Email address"
msgstr "Email адрес"
'''
        
        with open(PO_FILE, 'w', encoding='utf-8') as f:
            f.write(minimal_po)
    
    # Создаем .mo файл
    create_mo_file(PO_FILE, MO_FILE)
    print("Готово! Перезапустите сервер Django.")