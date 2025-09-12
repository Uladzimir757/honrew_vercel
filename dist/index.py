# Файл: index.py (ФИНАЛЬНАЯ ВЕРСИЯ на Bottle)

# --- 1. СТАНДАРТНЫЕ ИМПОРТЫ ---
import os
import json
import uuid
import math
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from functools import wraps

# --- 2. СТОРОННИЕ БИБЛИОТЕКИ ---
from bottle import Bottle, request, response, template, redirect
from jinja2 import Environment, FileSystemLoader, select_autoescape
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from aiohttp.wsgi import WSGIHandler # Для асинхронного запуска Bottle

# --- 3. ВСТРОЕННЫЙ КОД ИЗ ВАШЕГО ПРОЕКТА ---
class Settings:
    ITEMS_PER_PAGE: int = 10
settings = Settings()

def logger_info(message): print(f"INFO: {message}")
def logger_error(message): print(f"ERROR: {message}")

def get_password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}${pwd_hash.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt_hex, hash_hex = hashed_password.split('$')
        salt = bytes.fromhex(salt_hex)
        stored_hash = bytes.fromhex(hash_hex)
        new_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(new_hash, stored_hash)
    except Exception: return False

class D1Manager:
    def __init__(self, db): self.db = db
    async def execute(self, q, p=()): return await self.db.prepare(q).bind(*p).run()
    async def fetch_one(self, q, p=()): return await self.db.prepare(q).bind(*p).first()
    async def fetch_all(self, q, p=()):
        res = await self.db.prepare(q).bind(*p).all()
        return res.get('results', []) if res else []
    async def fetch_val(self, q, p=()):
        res = await self.db.prepare(q).bind(*p).first()
        return next(iter(res.values())) if res else 0

# --- 4. ГЛОБАЛЬНАЯ НАСТРОЙКА ---
app = Bottle()
admin_app = Bottle()
app.mount('/admin', admin_app)

_template_env = None
def get_template_env():
    global _template_env
    if _template_env is None:
        _template_env = Environment(
            loader=FileSystemLoader("app/templates"),
            autoescape=select_autoescape(['html', 'xml']),
            enable_async=True
        )
    return _template_env

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY: raise RuntimeError("SECRET_KEY не установлен!")
session_signer = URLSafeTimedSerializer(SECRET_KEY, salt='cookie-session')

# --- 5. MIDDLEWARE И УПРАВЛЕНИЕ СЕССИЯМИ ---
# Этот "плагин" будет внедрять объекты D1, R2 и сессии в каждый запрос
# чтобы они были доступны внутри роутов через объект `request`.
@app.hook('before_request')
@admin_app.hook('before_request')
async def setup_request_context():
    # 'env' берется из окружения, которое мы установим в on_fetch
    env = request.environ.get('cloudflare.env')
    request.db = D1Manager(env.DB)
    request.r2 = env.R2_BUCKET
    
    session_data = {}
    token = request.get_cookie("session")
    if token:
        try:
            session_data = session_signer.loads(token, max_age=86400)
        except (SignatureExpired, BadTimeSignature):
            session_data = {}
    request.session = session_data
    
    user_id = session_data.get("user_id")
    request.user = await request.db.fetch_one("SELECT * FROM users WHERE id = ?1", (user_id,)) if user_id else None
    
    # ... Ваша логика для языков и переводов ...
    
    # Flash сообщения
    request.flash = request.session.pop('flash', None)

@app.hook('after_request')
@admin_app.hook('after_request')
def save_session():
    # Сохраняем изменения в сессии в куки
    if 'session' in request and request.session:
        token = session_signer.dumps(request.session)
        response.set_cookie("session", token, path="/", httponly=True, max_age=86400, samesite='lax')

# --- 6. ДЕКОРАТОРЫ ---
def login_required(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if not request.user:
            request.session['flash'] = {"category": "error", "message": "Login required"}
            return redirect("/login")
        return await f(*args, **kwargs)
    return decorated_function

# --- 7. РОУТЫ (примеры) ---
# Теперь роуты чистые - вся логика в middleware
@app.get("/")
async def home():
    templates = get_template_env()
    # Передаем нужные переменные в шаблон
    templates.globals['user'] = request.user
    templates.globals['flash'] = request.flash
    template = templates.get_template("index.html")
    html = await template.render_async(background_image="index.jpg")
    return html

@app.get("/search")
async def search_results():
    # Доступ к базе данных через request.db
    total_items = await request.db.fetch_val("SELECT COUNT(*) FROM videos")
    # ... ваша логика ...
    return f"Найдено {total_items} видео."

@app.post("/register")
async def handle_registration():
    email = request.forms.get('email')
    password = request.forms.get('password')
    # ... ваша логика ...
    if password != request.forms.get('confirm_password'):
        request.session['flash'] = {"category": "error", "message": "Пароли не совпадают"}
        return redirect("/register")
    
    hashed_password = get_password_hash(password)
    await request.db.execute("INSERT INTO users (email, hashed_password) VALUES (?1, ?2)", (email, hashed_password))

    request.session['flash'] = {"category": "success", "message": "Регистрация успешна!"}
    return redirect("/login")

# !!! ВАЖНО !!!
# Вставьте сюда все остальные ваши роуты, адаптировав их под Bottle:
# 1. `@router.get(...)` -> `@app.get(...)`
# 2. Уберите `(request, env)` из аргументов функций.
# 3. Доступ к БД: `context['db']` -> `request.db`.
# 4. Доступ к пользователю: `context['user']` -> `request.user`.
# 5. Получение данных из формы: `(await request.formData()).get('email')` -> `request.forms.get('email')`.
# 6. Flash-сообщения и редирект: `make_redirect(...)` -> `request.session['flash'] = ...; redirect('/url')`.
# 7. Рендеринг шаблона: `return await templates.get_template(...).render_async(...)`.

# --- 8. ТОЧКА ВХОДА ДЛЯ CLOUDFLARE ---
async def on_fetch(worker_request, env):
    """
    Главная и единственная точка входа, которую видит Cloudflare.
    Она адаптирует запрос и запускает наше Bottle-приложение.
    """
    class AppWithEnv:
        def __init__(self, app, env):
            self.app = app
            self.env = env
        def __call__(self, environ, start_response):
            environ['cloudflare.env'] = self.env
            return self.app(environ, start_response)

    # Оборачиваем наше приложение, чтобы передать в него 'env'
    app_with_env = AppWithEnv(app, env)
    
    # Используем стандартный ASGI/WSGI-адаптер
    handler = WSGIHandler(app_with_env)
    
    # Преобразуем Response от aiohttp обратно в Response от Cloudflare
    from pyodide.http import to_pyodide_response
    aio_response = await handler.handle_request(worker_request)
    return await to_pyodide_response(aio_response)