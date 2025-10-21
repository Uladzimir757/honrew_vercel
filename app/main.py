# Файл: app/main.py
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, session, g

from app.config import settings
from app.routers import (auth_bp, pages_bp, reviews_bp, users_bp, admin_bp)
from app.dependencies import get_current_user

class PostgresManager:
    def __init__(self, dsn):
        self.dsn = dsn
        self._connection = None

    def _get_connection(self):
        if self._connection is None:
            try:
                self._connection = psycopg2.connect(self.dsn)
            except psycopg2.OperationalError as e:
                print(f"Database connection error: {e}")
                raise
        return self._connection

    def execute(self, query, params=None):
        conn = self._get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            conn.commit()
            return cursor

    def execute_and_fetch_one(self, query, params=None):
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            conn.commit()
            return result

    def fetch_one(self, query, params=None):
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    def fetch_all(self, query, params=None):
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def close(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None

def get_app():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_folder_path = os.path.join(project_root, 'static')

    app = Flask(__name__,
                static_folder=static_folder_path,
                static_url_path='/static',
                template_folder='templates')

    app.secret_key = settings.SECRET_KEY

    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_bp)

    @app.before_request
    def before_request_handler():
        g.db = PostgresManager(settings.DATABASE_URL)

        supported_langs = ['en', 'ru', 'pl']
        default_lang = 'en'  # --- Английский по умолчанию ---

        # 1. Проверяем параметр URL
        lang = request.args.get('lang')

        # 2. Если в URL нет, проверяем сессию
        if lang is None:
            lang = session.get('lang')

        # 3. Если и в сессии нет, пытаемся определить по заголовкам браузера
        if lang is None:
            # request.accept_languages возвращает предпочтения браузера
            # best_match выбирает лучший поддерживаемый язык из списка supported_langs
            lang = request.accept_languages.best_match(supported_langs)

        # 4. Если определить не удалось (браузер предложил неподдерживаемый язык), используем английский
        if lang is None:
            lang = default_lang

        # 5. Финальная проверка: если язык все еще невалидный
        if lang not in supported_langs:
            lang = default_lang

        # Сохраняем язык в сессию и g
        session['lang'] = lang
        g.lang = lang

        translations_path = os.path.join(app.root_path, 'locales', f'{lang}.json')
        try:
            with open(translations_path, 'r', encoding='utf-8') as f:
                g.tr = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Если файл перевода не найден, загружаем английский как запасной
            try:
                 fallback_path = os.path.join(app.root_path, 'locales', f'{default_lang}.json')
                 with open(fallback_path, 'r', encoding='utf-8') as f:
                     g.tr = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                 g.tr = {} # Оставляем пустым, если даже английский не найден

        g.user = get_current_user()
        g.flash = session.pop('flash', None)

    @app.teardown_request
    def teardown_request_handler(exception=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    @app.context_processor
    def inject_global_vars():
        pending_complaints_count = 0
        user = g.get('user')
        if user and user.get('is_admin'):
            try:
                # Используем базу данных из g, которая будет закрыта в teardown_request
                db = g.get('db')
                if db:
                    count_result = db.fetch_one(
                        "SELECT COUNT(*) as count FROM complaints WHERE status = 'pending'"
                    )
                    if count_result:
                        pending_complaints_count = count_result['count']
            except Exception as e:
                # Используем logger для записи ошибки
                app.logger.error(f"Error counting complaints: {e}")
                pending_complaints_count = 0 # Безопасное значение по умолчанию

        categories_nav = []
        try:
            # Используем базу данных из g
            db = g.get('db')
            if db:
                 categories_nav = db.fetch_all("SELECT name, slug FROM categories ORDER BY name")
        except Exception as e:
             app.logger.error(f"Error fetching categories for navbar: {e}")
             # Оставляем categories_nav пустым списком

        return {
            'user': user,
            'lang': g.get('lang'),
            'tr': g.get('tr'),
            'flash': g.get('flash'),
            'settings': settings,
            'pending_complaints_count': pending_complaints_count,
            'categories_for_nav': categories_nav
        }
    return app

# Этот блок гарантирует, что при прямом запуске файла  app создается
# Но при импорте из index.py (как делает Vercel), используется уже созданный app
if __name__ == "__main__":
    # Локальный запуск для отладки
    # Не будет выполняться на Vercel
    local_app = get_app()
    local_app.run(debug=True, port=8080)
elif __name__ != "__main__":
    # Этот блок выполняется при импорте, например, Vercel
    app = get_app()