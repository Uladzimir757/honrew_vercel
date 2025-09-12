import typer
import asyncio
from sqlalchemy import create_engine

from app.database import database, users, metadata
from app.security import get_password_hash
from app.config import settings

app = typer.Typer()

@app.command()
def init_db():
    """
    Инициализирует базу данных: создает все таблицы.
    """
    # Для создания таблиц нужен синхронный движок
    sync_database_url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_database_url)
    print("Создание таблиц в базе данных...")
    metadata.create_all(engine)
    print("Таблицы успешно созданы.")

@app.command()
def create_user(email: str, password: str):
    """
    Создает нового, сразу верифицированного пользователя.
    """
    async def _create_user():
        await database.connect()
        hashed_password = get_password_hash(password)
        query = users.insert().values(
            email=email, 
            hashed_password=hashed_password, 
            is_verified=True, # Сразу делаем верифицированным для удобства
            is_admin=False
        )
        try:
            user_id = await database.execute(query)
            print(f"Пользователь {email} (ID: {user_id}) успешно создан.")
        except Exception as e:
            print(f"Ошибка при создании пользователя: {e}")
        finally:
            await database.disconnect()
            
    asyncio.run(_create_user())

@app.command()
def create_admin(email: str):
    """
    Назначает существующего пользователя администратором.
    """
    async def _create_admin():
        await database.connect()
        query = users.select().where(users.c.email == email)
        user = await database.fetch_one(query)

        if not user:
            print(f"Ошибка: Пользователь с email '{email}' не найден.")
            await database.disconnect()
            return

        if user.is_admin:
            print(f"Пользователь {email} уже является администратором.")
            await database.disconnect()
            return
            
        update_query = users.update().where(users.c.id == user.id).values(is_admin=True)
        await database.execute(update_query)
        print(f"Успех! Пользователь {email} теперь администратор.")
        await database.disconnect()

    asyncio.run(_create_admin())


if __name__ == "__main__":
    app()