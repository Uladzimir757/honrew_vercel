# Файл: app/decorators.py
from functools import wraps
from flask import g, session, redirect, url_for, abort

def login_required(f):
    """
    Декоратор для проверки, что пользователь авторизован.
    Если нет - перенаправляет на страницу входа.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user:
            session["flash"] = {"category": "error", "message": g.tr.get("error_login_required")}
            return redirect(url_for('auth.handle_login', lang=session.get('lang')))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Декоратор для проверки, что пользователь является администратором.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user or not g.user.get("is_admin"):
            abort(403)  # Отказать в доступе (Forbidden)
        return f(*args, **kwargs)
    return decorated_function