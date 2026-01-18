# app/decorators.py (Полностью замените)
from functools import wraps
from flask import session, redirect, url_for, g
from app.database import db_manager # Нужно для param_style
from flask_login import current_user
def _get_param_placeholder():
    return "?" if db_manager.param_style == 'qmark' else "%s"

from flask_login import current_user

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            try:
                error_msg = g.tr["error_login_required"]
            except (KeyError, AttributeError):
                # Если перевод не найден или g.tr не существует
                error_msg = "Please log in to access this page."
            
            session["flash"] = {
                "category": "error", 
                "message": error_msg
            }
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            lang = session.get('lang', 'ru')
            session["flash"] = {"category": "error", "message": g.tr["error_login_required"]}
            return redirect(url_for('auth.handle_login', lang=lang))
        
        user_id = session['user_id']
        param_ph = _get_param_placeholder() # Используем хелпер
        user_data = g.db.fetch_one(f"SELECT is_admin FROM users WHERE id = {param_ph}", (user_id,))
        
        if not user_data or not user_data['is_admin']:
            lang = session.get('lang', 'ru')
            session["flash"] = {"category": "error", "message": g.tr["error_access_denied"]}
            return redirect(url_for('pages.home', lang=lang)) 
            
        return f(*args, **kwargs)
    return decorated_function
