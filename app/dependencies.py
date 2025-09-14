# Файл: app/dependencies.py

import json
from pathlib import Path
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

from app.d1_manager import d1_manager

# --- Функции для доступа к ресурсам Cloudflare ---

def get_d1_manager(request: Request) -> D1Manager:
    """Получает доступ к базе данных D1 из окружения воркера."""
    try:
        return D1Manager(request.scope['env'].DB)
    except (KeyError, AttributeError):
        raise RuntimeError("Байндинг D1 'DB' не найден. Убедитесь, что он прописан в wrangler.toml")

def get_r2_bucket(request: Request):
    """Получает доступ к бакету R2 из окружения воркера."""
    try:
        return request.scope['env'].R2_BUCKET
    except (KeyError, AttributeError):
        raise RuntimeError("Байндинг R2 'R2_BUCKET' не найден. Убедитесь, что он прописан в wrangler.toml")

def get_kv(request: Request):
    """Получает доступ к KV хранилищу из окружения воркера."""
    try:
        return request.scope['env'].KV
    except (KeyError, AttributeError):
        raise RuntimeError("Байндинг KV 'KV' не найден. Убедитесь, что он прописан в wrangler.toml")

# --- Управление языком и переводами ---

# Кэшируем переводы в памяти, чтобы не читать файлы каждый раз
_translations_cache = {}
locales_path = Path("locales")

def get_language_and_translations(request: Request) -> tuple[str, dict]:
    """Определяет язык и загружает соответствующий файл перевода."""
    lang = request.query_params.get("lang", request.session.get("lang", "en"))
    
    if lang not in _translations_cache:
        try:
            # Путь теперь относительно корня, где запускается воркер
            with open(f"locales/{lang}.json", "r", encoding="utf-8") as f:
                _translations_cache[lang] = json.load(f)
        except FileNotFoundError:
            # Если файл не найден, используем английский по умолчанию
            with open("locales/en.json", "r", encoding="utf-8") as f:
                _translations_cache["en"] = json.load(f)
            _translations_cache[lang] = _translations_cache["en"]
            lang = "en"
            
    request.session["lang"] = lang
    return lang, _translations_cache[lang]

# --- Аутентификация и авторизация ---

async def get_current_user(request: Request, db: D1Manager = Depends(get_d1_manager)) -> dict | None:
    """
    Проверяет сессию и возвращает полные данные пользователя из D1.
    Если пользователь не залогинен, возвращает None.
    """
    user_session = request.session.get("user")
    if not user_session or "id" not in user_session:
        return None
    
    user_id = user_session["id"]
    user = await db.fetch_one("SELECT * FROM users WHERE id = ?1", (user_id,))
    return user

async def require_user(request: Request, user: dict | None = Depends(get_current_user)) -> dict:
    """
    Требует, чтобы пользователь был залогинен.
    Если нет - перенаправляет на страницу логина.
    """
    if not user:
        lang, tr = get_language_and_translations(request)
        flash_message = tr.get("error_login_required", "Please log in to access this page.")
        request.session["flash"] = {"category": "error", "message": flash_message}
        # В FastAPI 303 редирект после POST, а здесь можно 302
        raise HTTPException(status_code=302, headers={"Location": f"/login?lang={lang}"})
    return user

async def require_admin_user(user: dict = Depends(require_user)) -> dict:
    """
    Требует, чтобы пользователь был не просто залогинен, но и являлся администратором.
    """
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# --- Контекст для шаблонов Jinja2 ---

async def get_template_context(request: Request, db: D1Manager = Depends(get_d1_manager)) -> dict:
    """Собирает все необходимые данные для рендеринга любой страницы."""
    lang, tr = get_language_and_translations(request)
    user = await get_current_user(request, db)
    
    flash_messages = request.session.pop("flash", None)
    
    return {
        "request": request,
        "user": user,
        "lang": lang,
        "tr": tr,
        "flash": flash_messages,
        "base_url": str(request.base_url)
    }