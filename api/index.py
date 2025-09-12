# Файл: api/index.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
import sys
import os

# --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
# Добавляем корневую папку проекта в путь, где Python ищет модули.
# Это позволит найти папку 'app'.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# -------------------------

# Теперь этот импорт сработает
from app.main import get_app

# Vercel ищет WSGI-совместимый объект с именем 'app'
# Мы вызываем нашу фабрику, чтобы его получить
app = get_app()