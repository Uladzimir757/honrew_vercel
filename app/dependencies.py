# Файл: app/dependencies.py
from flask import session

def get_current_user(db):
    user_session = session.get('user')
    if not user_session or 'id' not in user_session:
        return None
    
    user_data = db.fetch_one("SELECT * FROM users WHERE id = %s", (user_session['id'],))
    return user_data