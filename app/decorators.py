# Файл: app/decorators.py

from functools import wraps
from flask import g, redirect, url_for, request

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            lang = request.args.get('lang', 'ru')
            return redirect(url_for('auth.login', lang=lang))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # --- НАЧАЛО ОТЛАДОЧНОГО КОДА ---
        print("--- DEBUG: ЗАПУСК ПРОВЕРКИ АДМИНА ---")
        if 'user' in g and g.user is not None:
            print(f"--- DEBUG: Пользователь найден в g: {g.user}")
            print(f"--- DEBUG: Тип g.user: {type(g.user)}")
            is_admin_value = g.user.get('is_admin')
            print(f"--- DEBUG: Значение is_admin: {is_admin_value}")
            print(f"--- DEBUG: Тип значения is_admin: {type(is_admin_value)}")
        else:
            print("--- DEBUG: Пользователь в g не найден или None.")
        # --- КОНЕЦ ОТЛАДОЧНОГО КОДА ---

        if g.user is None or not g.user.get('is_admin'):
            print("--- DEBUG: ДОСТУП ЗАПРЕЩЁН ---")
            return "Forbidden: You don't have permission to access this resource.", 403
        
        print("--- DEBUG: ДОСТУП РАЗРЕШЁН ---")
        return f(*args, **kwargs)
    return decorated_function