# Файл: app/dependencies.py

from flask import session, g

def get_current_user():
    """
    Получает текущего пользователя из сессии и базы данных.
    Возвращает объект пользователя или None, если пользователь не авторизован.
    """
    user_id = session.get('user_id')
    if not user_id:
        return None

    if 'user' in g and g.user and g.user.get('id') == user_id:
        return g.user

    try:
        query = "SELECT * FROM users WHERE id = %s"
        user = g.db.fetch_one(query, (user_id,))
        if user:
            g.user = user
            return user
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None
            
    return None