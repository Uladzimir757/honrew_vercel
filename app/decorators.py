# app/decorators.py
from functools import wraps
from flask import session, redirect, url_for, g
from app.database import db_manager

def _get_param_placeholder():
    """Returns SQL parameter placeholder"""
    return "?" if db_manager.param_style == 'qmark' else "%s"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated via session
        if 'user_id' not in session:
            # Safely get error message
            error_msg = "Please login to continue"
            
            try:
                if hasattr(g, 'tr') and g.tr and isinstance(g.tr, dict):
                    error_msg = g.tr.get("error_login_required", error_msg)
            except:
                pass  # Keep default error message
            
            # Save error message
            session["flash"] = {
                "category": "error", 
                "message": error_msg
            }
            
            # Get language from request or session
            lang = kwargs.get('lang') or g.get('lang', session.get('lang', 'en'))
            # Use correct endpoint name
            return redirect(url_for("auth.handle_login", lang=lang))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check authentication
        if 'user_id' not in session:
            error_msg = "Please login to continue"
            
            try:
                if hasattr(g, 'tr') and g.tr and isinstance(g.tr, dict):
                    error_msg = g.tr.get("error_login_required", error_msg)
            except:
                pass
            
            session["flash"] = {
                "category": "error", 
                "message": error_msg
            }
            
            lang = kwargs.get('lang') or g.get('lang', session.get('lang', 'en'))
            return redirect(url_for('auth.handle_login', lang=lang))
        
        # Check admin privileges
        user_id = session['user_id']
        param_ph = _get_param_placeholder()
        
        try:
            user_data = g.db.fetch_one(f"SELECT is_admin FROM users WHERE id = {param_ph}", (user_id,))
            
            if not user_data or not user_data.get('is_admin'):
                error_msg = "Access denied"
                
                try:
                    if hasattr(g, 'tr') and g.tr and isinstance(g.tr, dict):
                        error_msg = g.tr.get("error_access_denied", error_msg)
                except:
                    pass
                
                session["flash"] = {
                    "category": "error", 
                    "message": error_msg
                }
                
                lang = kwargs.get('lang') or g.get('lang', session.get('lang', 'en'))
                return redirect(url_for('pages.home', lang=lang))
                
        except Exception as e:
            # If database query error
            session["flash"] = {
                "category": "error", 
                "message": f"Error checking permissions: {str(e)}"
            }
            
            lang = kwargs.get('lang') or g.get('lang', session.get('lang', 'en'))
            return redirect(url_for('pages.home', lang=lang))
        
        return f(*args, **kwargs)
    return decorated_function
