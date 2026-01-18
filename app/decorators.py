# app/decorators.py
from functools import wraps
from flask import session, redirect, url_for, g
from app.database import db_manager

def _get_param_placeholder():
    """Возвращает placeholder для параметров SQL запроса"""
    return "?" if db_manager.param_style == 'qmark' else "%s"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Проверяем, авторизован ли пользователь через session
        if 'user_id' not in session:
            try:
                # Безопасно получаем сообщение об ошибке
                if hasattr(g, 'tr') and g.tr and isinstance(g.tr, dict):
                    error_msg = g.tr.get("error_login_required", "Для выполнения этого действия необходимо войти в систему.")
                else:
                    error_msg = "Для выполнения этого действия необходимо войти в систему."
            except:
                error_msg = "Для выполнения этого действия необходимо войти в систему."
            
            # Сохраняем сообщение об ошибке
            session["flash"] = {
                "category": "error", 
                "message": error_msg
            }
            
            # Получаем язык из запроса или сессии
            lang = kwargs.get('lang') or g.get('lang', session.get('lang', 'ru'))
            return redirect(url_for("auth.login", lang=lang))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Сначала проверяем авторизацию
        if 'user_id' not in session:
            try:
                if hasattr(g, 'tr') and g.tr and isinstance(g.tr, dict):
                    error_msg = g.tr.get("error_login_required", "Для выполнения этого действия необходимо войти в систему.")
                else:
                    error_msg = "Для выполнения этого действия необходимо войти в систему."
            except:
                error_msg = "Для выполнения этого действия необходимо войти в систему."
            
            session["flash"] = {
                "category": "error", 
                "message": error_msg
            }
            
            lang = kwargs.get('lang') or g.get('lang', session.get('lang', 'ru'))
            return redirect(url_for('auth.login', lang=lang))
        
        # Проверяем права администратора
        user_id = session['user_id']
        param_ph = _get_param_placeholder()
        
        try:
            user_data = g.db.fetch_one(f"SELECT is_admin FROM users WHERE id = {param_ph}", (user_id,))
            
            if not user_data or not user_data.get('is_admin'):
                try:
                    if hasattr(g, 'tr') and g.tr and isinstance(g.tr, dict):
                        error_msg = g.tr.get("error_access_denied", "Доступ запрещен.")
                    else:
                        error_msg = "Доступ запрещен."
                except:
                    error_msg = "Доступ запрещен."
                
                session["flash"] = {
                    "category": "error", 
                    "message": error_msg
                }
                
                lang = kwargs.get('lang') or g.get('lang', session.get('lang', 'ru'))
                return redirect(url_for('pages.home', lang=lang))
                
        except Exception as e:
            # Если ошибка при запросе к БД
            session["flash"] = {
                "category": "error", 
                "message": f"Ошибка проверки прав: {str(e)}"
            }
            
            lang = kwargs.get('lang') or g.get('lang', session.get('lang', 'ru'))
            return redirect(url_for('pages.home', lang=lang))
        
        return f(*args, **kwargs)
    return decorated_function
