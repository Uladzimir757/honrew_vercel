# Файл: app/dependencies.py
import json
from flask import request, session, g

def get_language_and_translations(req):
    """
    Определяет язык и загружает переводы.
    Предполагается, что переводы предзагружены в g.translations в main.py.
    """
    # Определяем язык из GET-параметра, сессии или по умолчанию
    lang = req.args.get('lang', session.get('lang', 'en'))
    if lang not in ['en', 'ru', 'pl']:
        lang = 'en'
    session['lang'] = lang
    
    # g.tr устанавливается в before_request в main.py, здесь мы его просто используем
    translations = g.get('tr', {})
    return lang, translations

def get_current_user(db):
    """
    Получает текущего пользователя из сессии, используя переданный объект подключения к БД.
    """
    user_session = session.get('user')
    if not user_session or 'id' not in user_session:
        return None
    
    # Используем переданный объект `db` (который является g.db)
    user_data = db.fetch_one("SELECT * FROM users WHERE id = %s", (user_session['id'],))
    return user_data