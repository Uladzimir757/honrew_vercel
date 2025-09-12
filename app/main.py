# Файл: app/main.py (ПОЛНАЯ И ФИНАЛЬНАЯ ВЕРСИЯ)
import os
import json
import psycopg2
import re
from psycopg2.extras import RealDictCursor
from flask import Flask, request, session, g

# --- Класс для работы с PostgreSQL ---
# Этот класс-адаптер имитирует методы D1Manager для минимальных изменений в роутах
class PostgresManager:
    def __init__(self, conn):
        self.conn = conn

    def _execute_query(self, query, params=(), fetch=None):
        # D1 использует ?1, ?2 для параметров, psycopg2 использует %s.
        # Простое авто-замещение для совместимости.
        query = re.sub(r'\?(\d+)', r'%s', query)
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            if fetch == 'one':
                return cursor.fetchone()
            if fetch == 'all':
                return cursor.fetchall()
            
            # Для INSERT, UPDATE, DELETE
            self.conn.commit()
            return {'meta': {'changes': cursor.rowcount}}

    def fetch_one(self, query, params=()):
        return self._execute_query(query, params, fetch='one')

    def fetch_all(self, query, params=()):
        return self._execute_query(query, params, fetch='all')

    def execute(self, query, params=()):
        return self._execute_query(query, params)

# --- Глобальная переменная для хранения приложения (фабричный паттерн) ---
_app = None

def get_app():
    """
    Создает и настраивает экземпляр приложения Flask.
    """
    global _app
    if _app is None:
        # Указываем Flask, что шаблоны и статика лежат в папке /app/
        # Vercel скопирует эту папку в корень сборки.
        _app = Flask(__name__, instance_relative_config=True,
                     template_folder='templates', static_folder='static')

        # --- Загрузка конфигурации из переменных окружения Vercel ---
        SECRET_KEY = os.environ.get('SECRET_KEY')
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not SECRET_KEY or not DATABASE_URL:
            raise ValueError("SECRET_KEY и DATABASE_URL должны быть установлены в настройках Vercel!")
        _app.secret_key = SECRET_KEY
        
        # --- Регистрация всех частей приложения (Blueprints) ---
        # Импорты должны быть относительными (с точкой), так как main.py теперь внутри пакета 'app'
        from .routers.pages import pages_bp
        from .routers.auth import auth_bp
        from .routers.users import users_bp
        from .routers.videos import videos_bp
        from .routers.admin import admin_bp
        from .routers.complaints import complaints_bp
        
        _app.register_blueprint(pages_bp)
        _app.register_blueprint(auth_bp)
        _app.register_blueprint(users_bp)
        _app.register_blueprint(videos_bp)
        _app.register_blueprint(admin_bp)
        _app.register_blueprint(complaints_bp)
        
        # --- Обработчики, выполняющиеся перед и после каждого запроса ---
        @_app.before_request
        def before_request_handler():
            """Создает подключение к БД и загружает данные пользователя для каждого запроса."""
            db_conn = psycopg2.connect(DATABASE_URL)
            g.db = PostgresManager(db_conn)
            
            user_id = session.get("user", {}).get("id")
            g.user = g.db.fetch_one("SELECT * FROM users WHERE id = %s", (user_id,)) if user_id else None
            
            lang = request.args.get("lang", session.get("lang", "en"))
            if lang not in ['en', 'ru']:
                lang = 'en'
            session["lang"] = lang
            
            # Логика загрузки переводов
            try:
                # Путь нужно строить от текущего файла
                dir_path = os.path.dirname(os.path.realpath(__file__))
                with open(os.path.join(dir_path, f"locales/{lang}.json"), "r", encoding="utf-8") as f:
                    g.tr = json.load(f)
            except FileNotFoundError:
                dir_path = os.path.dirname(os.path.realpath(__file__))
                with open(os.path.join(dir_path, "locales/en.json"), "r", encoding="utf-8") as f:
                    g.tr = json.load(f)
            
            g.flash = session.pop("flash", None)

        @_app.teardown_request
        def teardown_request(exception=None):
            """Закрывает соединение с БД после каждого запроса."""
            db_conn_manager = getattr(g, 'db', None)
            if db_conn_manager is not None:
                db_conn_manager.conn.close()

        @_app.context_processor
        def inject_global_context():
            """Делает переменные доступными во всех шаблонах Jinja2."""
            return {
                'user': getattr(g, 'user', None),
                'tr': getattr(g, 'tr', {}),
                'flash': getattr(g, 'flash', None),
                'lang': session.get('lang', 'en')
            }
            
    return _app