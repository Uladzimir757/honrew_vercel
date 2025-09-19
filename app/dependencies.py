# Файл: app/dependencies.py

import json
import os
from flask import request, session, g

# --- Глобальные переменные для переводов ---
LOCALES_DIR = os.path.join(os.path.dirname(__file__), 'locales')
DEFAULT_LANG = 'ru'
_translations_cache = {}


def load_translations(lang: str) -> dict:
    """
    Загружает файл перевода для указанного языка.
    Использует кэш для производительности.
    """
    if lang in _translations_cache:
        return _translations_cache[lang]

    try:
        file_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        with open(file_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            _translations_cache[lang] = translations
            return translations
    except (FileNotFoundError, json.JSONDecodeError):
        if lang != DEFAULT_LANG:
            return load_translations(DEFAULT_LANG)
        return {}


def get_language_and_translations(req: request):
    """
    Определяет язык из параметра запроса (?lang=...) и загружает переводы.
    """
    lang = req.args.get('lang', DEFAULT_LANG)
    translations = load_translations(lang)
    return lang, translations


### НАЧАЛО НОВОГО КОДА ###

def get_current_user():
    """
    Получает текущего пользователя из сессии и базы данных.
    Возвращает объект пользователя или None, если пользователь не авторизован.
    """
    user_id = session.get('user_id')
    if not user_id:
        return None

    # Проверяем, не был ли пользователь уже загружен в этом запросе
    if 'user' in g and g.user and g.user.get('id') == user_id:
        return g.user

    # Загружаем пользователя из базы данных
    # ВАЖНО: Запрос предполагает, что у вас есть таблица 'users' с колонкой 'id'
    try:
        query = "SELECT * FROM users WHERE id = %s"
        user = g.db.fetch_one(query, (user_id,))
        if user:
            # Сохраняем пользователя в контексте запроса 'g', чтобы не делать лишних запросов к БД
            g.user = user
            return user
    except Exception as e:
        # В случае ошибки базы данных или другой проблемы
        print(f"Error fetching user: {e}") # Используем print, т.к. logger может быть недоступен
        return None
            
    return None

### КОНЕЦ НОВОГО КОДА ###