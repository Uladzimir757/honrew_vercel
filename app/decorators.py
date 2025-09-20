# Файл: app/decorators.py

from functools import wraps
from flask import g, redirect, url_for, request

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            # Сохраняем язык при редиректе
            lang = request.args.get('lang', 'ru')
            return redirect(url_for('auth.login', lang=lang))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Проверяем наличие пользователя и его права через .get(), как у словаря
        if g.user is None or not g.user.get('is_admin'):
            # Если нет прав, возвращаем ошибку 403 Forbidden
            return "Forbidden: You don't have permission to access this resource.", 403
        return f(*args, **kwargs)
    return decorated_function