# app/decorators.py (Полностью замените)
from functools import wraps
from flask import session, redirect, url_for, g
from app.database import db_manager # Нужно для param_style

def _get_param_placeholder():
    return "?" if db_manager.param_style == 'qmark' else "%s"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            lang = session.get('lang', 'ru') # Получаем язык из сессии
            session["flash"] = {"category": "error", "message": g.tr["error_login_required"]}
            return redirect(url_for('auth.handle_login', lang=lang)) 
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