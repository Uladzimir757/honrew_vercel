# Файл: api/index.py (ФИНАЛЬНАЯ ВЕРСИЯ)
import sys
import os

# --- КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ ---
# Эта строка добавляет корневую папку проекта в путь, где Python ищет модули.
# Это позволит найти папку 'app'.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# -------------------------

# Теперь этот импорт сработает
# Важно: в вашем файле app/main.py используется функция get_app()
from app.main import get_app

# Vercel ищет WSGI-совместимый объект с именем 'app'
app = get_app()