# Файл: app/dependencies.py

import json
import os
from flask import request

# --- Глобальные переменные для переводов ---
# Определяем путь к папке с файлами переводов (locales)
LOCALES_DIR = os.path.join(os.path.dirname(__file__), 'locales')
DEFAULT_LANG = 'ru'  # Язык по умолчанию

# Кэш для хранения загруженных переводов, чтобы не читать файлы каждый раз
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
        # Если файл для языка не найден или он некорректен,
        # возвращаем переводы для языка по умолчанию.
        if lang != DEFAULT_LANG:
            return load_translations(DEFAULT_LANG)
        return {}


def get_language_and_translations(req: request):
    """
    Определяет язык из параметра запроса (?lang=...) и загружает переводы.
    Эта функция будет использоваться во всех маршрутах.
    """
    # Получаем язык из URL, если его нет — используем язык по умолчанию
    lang = req.args.get('lang', DEFAULT_LANG)
    
    # Загружаем словарь с переводами для этого языка
    translations = load_translations(lang)
    
    return lang, translations