# Это пример того, как будет выглядеть ваш роутер auth.py после миграции.
# Обратите внимание на использование d1_manager и чистых SQL-запросов.

import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Form, Depends, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

# Убираем старые импорты, связанные с SQLAlchemy
# from app.database import database, users
from app.d1_manager import D1Manager # <-- Новый импорт
from app.security import get_password_hash, verify_password
from app.dependencies import get_template_context, get_language_and_translations
from app.config import settings

router = APIRouter(
    tags=["Authentication D1"]
)
templates = Jinja2Templates(directory="app/templates")


# Функция для получения D1Manager из контекста Worker'а
# FastAPI не может инжектировать его напрямую, поэтому получаем его из Request.
def get_d1_manager(request: Request) -> D1Manager:
    return D1Manager(request.state.env.DB)


@router.post("/register_d1")
async def handle_d1_registration(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    user_type: str = Form(...),
    consent: str = Form(None),
    db: D1Manager = Depends(get_d1_manager) # <-- Получаем наш D1Manager
):
    lang, tr = get_language_and_translations(request)

    # ... (все проверки остаются такими же)
    if password != confirm_password:
        # ...
        pass
        
    # Проверяем, существует ли пользователь, с помощью SQL-запроса
    existing_user_query = "SELECT id FROM users WHERE email = ?1"
    user_exists = await db.fetch_one(existing_user_query, (email,))

    if user_exists:
        request.session["flash"] = {"category": "error", "message": tr["error_user_exists"]}
        return RedirectResponse(url=f"/register?lang={lang}", status_code=303)

    hashed_password = get_password_hash(password)
    verification_token = secrets.token_urlsafe(32)

    # Вставляем нового пользователя с помощью SQL
    # Используем RETURNING id чтобы получить ID новой записи
    insert_query = """
        INSERT INTO users (email, hashed_password, verification_token, user_type, is_admin, is_verified)
        VALUES (?1, ?2, ?3, ?4, 0, 0)
        RETURNING id;
    """
    params = (email, hashed_password, verification_token, user_type)
    
    new_user_id = await db.execute(insert_query, params)

    if new_user_id:
        print(f"Новый пользователь с ID {new_user_id} создан.")
        # ... (логика отправки email остается такой же) ...
    else:
        print("Не удалось создать пользователя.")
        # ... (обработка ошибки) ...

    request.session["flash"] = {"category": "success", "message": tr["registration_check_email"]}
    return RedirectResponse(url=f"/login?lang={lang}", status_code=303)


### ### Ваши следующие шаги:

   # 1.  **Установите Wrangler** и авторизуйтесь в Cloudflare.
   # 2.  **Создайте D1 базу данных** с помощью `wrangler d1 create ...`.
   # 3.  **Примените схему:** Скопируйте ID и имя базы в `wrangler.toml`, а затем выполните команду, чтобы создать таблицы:
   #     ```bash
    #    wrangler d1 execute <DB_NAME> --file=./schema.sql
        
