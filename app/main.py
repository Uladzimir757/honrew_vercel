# Файл: app/main.py
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, session, g

from app.config import settings
from app.routers import (auth_bp, pages_bp, videos_bp, users_bp, 
                         complaints_bp, admin_bp)
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
                print(f"Ошибка подключения к базе данных: {e}")
                raise
        return self._connection

    def execute(self, query, params=None):
        conn = self._get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            conn.commit()
            return cursor

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
    # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
    # Определяем корневую директорию проекта
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Указываем новый путь к папке static в корне
    static_folder_path = os.path.join(project_root, 'static')

    # Создаем приложение Flask с указанием нового пути к static_folder
    app = Flask(__name__, 
                static_folder=static_folder_path, 
                static_url_path='/static',
                template_folder='templates')
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    app.secret_key = settings.SECRET_KEY

    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(videos_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(complaints_bp)
    app.register_blueprint(admin_bp)

    @app.before_request
    def before_request_handler():
        g.db = PostgresManager(settings.DATABASE_URL)
        
        lang = request.args.get('lang', session.get('lang', 'ru'))
        if lang not in ['en', 'ru', 'pl']:
            lang = 'ru'
        session['lang'] = lang
        g.lang = lang

        translations_path = os.path.join(app.root_path, 'locales', f'{lang}.json')
        try:
            with open(translations_path, 'r', encoding='utf-8') as f:
                g.tr = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            g.tr = {}
        
        g.user = get_current_user(g.db)
        g.flash = session.pop('flash', None)

    @app.teardown_request
    def teardown_request_handler(exception=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    @app.context_processor
    def inject_global_vars():
        return {
            'user': g.get('user'),
            'lang': g.get('lang'),
            'tr': g.get('tr'),
            'flash': g.get('flash'),
            'settings': settings
        }
    return app

if __name__ != "__main__":
    app = get_app()