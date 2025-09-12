import pytest
import pytest_asyncio  # <-- Важный импорт
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import metadata, database, settings
from app.dependencies import get_current_user

# Настраиваем тестовую базу данных в памяти (SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Переопределяем подключение к базе данных для тестов
settings.DATABASE_URL = TEST_DATABASE_URL
engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# Функция-заглушка для аутентифицированных тестов
async def override_get_current_user():
    return {"id": 1, "email": "test@example.com", "is_admin": False}

@pytest.fixture(scope="session")
def event_loop():
    """Создает экземпляр event loop для нашей тестовой сессии."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# ИЗМЕНЕНИЕ ЗДЕСЬ: используется @pytest_asyncio.fixture
@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_setup_and_teardown():
    """Создает и удаляет таблицы для каждого тестового запуска."""
    metadata.create_all(engine)
    await database.connect()
    yield
    await database.disconnect()
    metadata.drop_all(engine)

# ИЗМЕНЕНИЕ ЗДЕСЬ: используется @pytest_asyncio.fixture
@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncClient:
    """Создает тестовый клиент для отправки запросов."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# ИЗМЕНЕНИЕ ЗДЕСЬ: используется @pytest_asyncio.fixture
@pytest_asyncio.fixture(scope="function")
async def authenticated_client() -> AsyncClient:
    """Создает аутентифицированный тестовый клиент."""
    app.dependency_overrides[get_current_user] = override_get_current_user
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    # Очищаем переопределение после завершения теста
    app.dependency_overrides = {}