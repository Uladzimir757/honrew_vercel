# Файл: app/main.py (ФИНАЛЬНАЯ ВЕРСИЯ ДЛЯ VERCEL)
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, session, g

# --- Класс для работы с PostgreSQL ---
class PostgresManager:
    def __init__(self, conn):
        self.conn = conn

    def _execute_query(self, query, params=(), fetch=None):
        import re
        query = re.sub(r'\?(\d+)', r'%s', query)
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            if fetch == 'one':
                return cursor.fetchone()
            if fetch == 'all':
                return cursor.fetchall()
            self.conn.commit()
            return {'meta': {'changes': cursor.rowcount}}

    def fetch_one(self, query, params=()):
        return self._execute_query(query, params, fetch='one')

    def fetch_all(self, query, params=()):
        return self._execute_query(query, params, fetch='all')

    def execute(self, query, params=()):
        return self._execute_query(query, params)

# --- Глобальная переменная для хранения приложения ---
_app = None

def get_app():
    global _app
    if _app is None:
        _app = Flask(__name__)

        # --- Ключи из переменных окружения Vercel ---
        SECRET_KEY = os.environ.get('SECRET_KEY')
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not SECRET_KEY or not DATABASE_URL:
            raise ValueError("SECRET_KEY и DATABASE_URL должны быть установлены!")
        _app.secret_key = SECRET_KEY
        
        # --- Регистрация Blueprints ---
        from app.routers.pages import pages_bp
        # ... добавьте сюда импорты и регистрацию ВСЕХ ваших blueprints ...
        
        _app.register_blueprint(pages_bp)
        
        # --- Обработчики запросов ---
        @_app.before_request
        def before_request_handler():
            db_conn = psycopg2.connect(DATABASE_URL)
            g.db = PostgresManager(db_conn)
            
            user_id = session.get("user", {}).get("id")
            g.user = g.db.fetch_one("SELECT * FROM users WHERE id = %s", (user_id,)) if user_id else None
            
            lang = request.args.get("lang", session.get("lang", "en"))
            if lang not in ['en', 'ru']: lang = 'en'
            session["lang"] = lang
            
            # ... и так далее, ваша логика ...

        @_app.teardown_request
        def teardown_request(exception=None):
            db_conn = getattr(g, 'db', None)
            if db_conn is not None:
                db_conn.conn.close()

        @_app.context_processor
        def inject_global_context():
            return {
                'user': getattr(g, 'user', None),
                'lang': session.get('lang', 'en')
            }
            
    return _app