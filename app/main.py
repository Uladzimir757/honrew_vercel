# Файл: app/main.py
import os
import json
import psycopg2
import math # Добавлен импорт math, если его не было
from psycopg2.extras import RealDictCursor
from flask import Flask, request, session, g, url_for, render_template, redirect, abort # Добавлены импорты для полноты
from logging.config import dictConfig # Для логирования ошибок

from app.config import settings
from app.routers import (auth_bp, pages_bp, reviews_bp, users_bp, admin_bp)
from app.dependencies import get_current_user

# Настройка логирования Flask (если еще не настроено)
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


class PostgresManager:
    def __init__(self, dsn):
        self.dsn = dsn
        self._connection = None

    def _get_connection(self):
        if self._connection is None:
            try:
                self._connection = psycopg2.connect(self.dsn)
            except psycopg2.OperationalError as e:
                # Используем логгер Flask для записи ошибки
                current_app.logger.error(f"Database connection error: {e}")
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
        # --- Логика определения языка (с английским по умолчанию) ---
        g.db = PostgresManager(settings.DATABASE_URL)

        supported_langs = ['en', 'ru', 'pl']
        default_lang = 'en'

        lang = request.args.get('lang')
        if lang is None:
            lang = session.get('lang')
        if lang is None:
            lang = request.accept_languages.best_match(supported_langs)
        if lang is None:
            lang = default_lang
        if lang not in supported_langs:
            lang = default_lang

        session['lang'] = lang
        g.lang = lang
        # --- Конец логики определения языка ---

        # --- Загрузка переводов ---
        translations_path = os.path.join(app.root_path, 'locales', f'{lang}.json')
        try:
            with open(translations_path, 'r', encoding='utf-8') as f:
                g.tr = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            try:
                 fallback_path = os.path.join(app.root_path, 'locales', f'{default_lang}.json')
                 with open(fallback_path, 'r', encoding='utf-8') as f:
                     g.tr = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                 g.tr = {}
        # --- Конец загрузки переводов ---

        g.user = get_current_user()
        g.flash = session.pop('flash', None)

    @app.teardown_request
    def teardown_request_handler(exception=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    @app.context_processor
    def inject_global_vars():
        # --- Эта функция теперь с изменениями для nav_structure ---
        pending_complaints_count = 0
        user = g.get('user')
        db = g.get('db') # Получаем соединение с БД из g

        # --- Получаем счетчик жалоб ---
        if user and user.get('is_admin'):
            try:
                if db:
                    count_result = db.fetch_one(
                        "SELECT COUNT(*) as count FROM complaints WHERE status = 'pending'"
                    )
                    if count_result:
                        pending_complaints_count = count_result['count']
            except Exception as e:
                # Используем логгер Flask для записи ошибки
                app.logger.error(f"Error counting complaints: {e}")
                pending_complaints_count = 0 # Безопасное значение по умолчанию

        # --- Формируем структуру навигации с подкатегориями ---
        nav_structure = []
        try:
            if db:
                # 1. Получаем все основные категории
                main_categories = db.fetch_all("SELECT id, name, slug FROM categories ORDER BY name")
                # 2. Получаем все подкатегории
                all_subcategories = db.fetch_all(
                    "SELECT id, name, slug, category_id FROM subcategories ORDER BY name"
                )

                # 3. Группируем подкатегории по родительскому ID
                subcategories_by_parent = {}
                for subcat in all_subcategories:
                    parent_id = subcat['category_id']
                    if parent_id not in subcategories_by_parent:
                        subcategories_by_parent[parent_id] = []
                    subcategories_by_parent[parent_id].append(subcat)

                # 4. Собираем итоговую структуру
                for cat in main_categories:
                    nav_structure.append({
                        'main': cat,
                        'sub': subcategories_by_parent.get(cat['id'], []) # Получаем список подкатегорий или пустой список
                    })
        except Exception as e:
            app.logger.error(f"Error fetching categories/subcategories for navbar: {e}")
            nav_structure = [] # В случае ошибки - пустая навигация
        # --- Конец изменений для nav_structure ---

        return {
            'user': user,
            'lang': g.get('lang'),
            'tr': g.get('tr'),
            'flash': g.get('flash'),
            'settings': settings,
            'pending_complaints_count': pending_complaints_count,
            'nav_structure': nav_structure # Передаем новую структуру в шаблон
        }
        # --- Конец функции inject_global_vars ---

    return app

# Этот блок гарантирует, что при прямом запуске файла app создается
# Но при импорте из index.py (как делает Vercel), используется уже созданный app
if __name__ == "__main__":
    # Локальный запуск для отладки
    # Не будет выполняться на Vercel
    from flask import current_app # Добавляем импорт для локального запуска
    local_app = get_app()
    local_app.run(debug=True, port=8080)
elif __name__ != "__main__":
    # Этот блок выполняется при импорте, например, Vercel
    from flask import current_app # Добавляем импорт для использования app.logger
    app = get_app()