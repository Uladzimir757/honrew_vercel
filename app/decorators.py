# app/decorators.py
from functools import wraps
from flask import session, redirect, url_for, g
from flask_login import current_user
from app.database import db_manager

def _get_param_placeholder():
    """Возвращает placeholder для параметров SQL запроса"""
    return "?" if db_manager.param_style == 'qmark' else "%s"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            try:
                # Проверяем, существует ли g.tr
                if hasattr(g, 'tr') and g.tr:
                    error_msg = g.tr.get("error_login_required", "Please log in to access this page.")
                else:
                    error_msg = "Please log in to access this page."
            except (KeyError, AttributeError):
                error_msg = "Please log in to access this page."
            
            session["flash"] = {
                "category": "error", 
                "message": error_msg
            }
            
            # Получаем текущий язык из запроса или сессии
            lang = g.get('lang', session.get('lang', 'ru'))
            return redirect(url_for("auth.login", lang=lang))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Сначала проверяем авторизацию через Flask-Login
        if not current_user.is_authenticated:
            return login_required(f)(*args, **kwargs)
        
        # Проверяем права администратора через Flask-Login
        if not current_user.is_admin:
            try:
                if hasattr(g, 'tr') and g.tr:
                    error_msg = g.tr.get("error_access_denied", "Access denied.")
                else:
                    error_msg = "Access denied."
            except (KeyError, AttributeError):
                error_msg = "Access denied."
            
            session["flash"] = {
                "category": "error", 
                "message": error_msg
            }
            
            lang = g.get('lang', session.get('lang', 'ru'))
            return redirect(url_for('pages.home', lang=lang))
        
        # Альтернативная проверка через базу данных (если нужно)
        # param_ph = _get_param_placeholder()
        # user_data = g.db.fetch_one(f"SELECT is_admin FROM users WHERE id = {param_ph}", (current_user.id,))
        # if not user_data or not user_data['is_admin']:
        #     # обработка ошибки...
        
        return f(*args, **kwargs)
    return decorated_function
