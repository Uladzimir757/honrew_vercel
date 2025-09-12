# Файл: app/main.py
import os
import json
from flask import Flask, request, session, g
from app.d1_manager import D1Manager

# --- Глобальная переменная для хранения приложения ---
_app = None

def get_app():
    """
    Эта функция создает экземпляр Flask только один раз,
    при первом вызове, и затем возвращает его.
    """
    global _app
    if _app is None:
        _app = Flask(__name__)

        SECRET_KEY = os.environ.get('SECRET_KEY')
        if not SECRET_KEY:
            raise ValueError("Необходимо установить SECRET_KEY в переменных окружения!")
        _app.secret_key = SECRET_KEY
        
        # --- Регистрация Blueprints ---
        from app.routers.pages import pages_bp
        from app.routers.auth import auth_bp
        from app.routers.users import users_bp
        from app.routers.videos import videos_bp
        from app.routers.admin import admin_bp
        from app.routers.complaints import complaints_bp
        
        _app.register_blueprint(pages_bp)
        _app.register_blueprint(auth_bp)
        _app.register_blueprint(users_bp)
        _app.register_blueprint(videos_bp)
        _app.register_blueprint(admin_bp)
        _app.register_blueprint(complaints_bp)
        
        # --- Обработчик before_request и context_processor остаются внутри ---
        @_app.before_request
        def before_request_handler():
            try:
                g.db = D1Manager(request.environ['workers.bindings']['DB'])
                g.r2 = request.environ['workers.bindings']['R2_BUCKET']
                g.kv = request.environ['workers.bindings']['KV']
            except (KeyError, AttributeError):
                raise RuntimeError("Не удалось получить доступ к байндингам Cloudflare.")

            user_id = session.get("user", {}).get("id")
            g.user = g.db.fetch_one("SELECT * FROM users WHERE id = ?1", (user_id,)) if user_id else None
            
            lang = request.args.get("lang", session.get("lang", "en"))
            if lang not in ['en', 'ru']:
                lang = 'en'
            session["lang"] = lang
            
            try:
                with open(f"app/locales/{lang}.json", "r", encoding="utf-8") as f:
                    g.tr = json.load(f)
            except FileNotFoundError:
                with open("app/locales/en.json", "r", encoding="utf-8") as f:
                    g.tr = json.load(f)
            
            g.flash = session.pop("flash", None)

        @_app.context_processor
        def inject_global_context():
            return {
                'user': getattr(g, 'user', None),
                'tr': getattr(g, 'tr', {}),
                'flash': getattr(g, 'flash', None),
                'lang': session.get('lang', 'en')
            }
            
    return _app