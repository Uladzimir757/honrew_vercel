# tests/conftest.py (Полностью замените)
import pytest
from app.main import app as flask_app
from app.database import db_manager, DatabaseManager 
import os

@pytest.fixture(scope='session')
def app():
    original_db_manager_instance = db_manager # Сохраняем оригинальный экземпляр
    
    # Создаем новую конфигурацию для тестового приложения
    flask_app.config.from_mapping(
        TESTING=True,
        WTF_CSRF_ENABLED=False 
    )

    # Инициализируем **временный** DatabaseManager для тестов с SQLite
    test_db_url = 'sqlite:///./test.db'
    
    # Переопределяем глобальный db_manager на тестовый экземпляр
    # Это важно, чтобы все модули приложения использовали тестовую БД
    # Здесь мы модифицируем существующий глобальный экземпляр
    db_manager.__init__(test_db_url) 

    # Создаем таблицы в тестовой БД, используя схему для SQLite
    db_manager.recreate_tables(schema_file='schema_sqlite.sql') # Используем recreate_tables и указываем схему

    yield flask_app # Передаем экземпляр Flask приложения тестам

    # Восстанавливаем оригинальный db_manager после завершения всех тестов
    # Закрываем соединение тестовой БД перед восстановлением
    db_manager.close_connection() 
    db_manager.__init__(original_db_manager_instance.database_url) # Восстанавливаем оригинальный URL и state

    # Удаляем тестовый файл БД
    if os.path.exists('./test.db'):
        os.remove('./test.db')

@pytest.fixture(scope='function')
def client(app):
    """
    Фикстура, которая предоставляет тестовый клиент для каждого теста.
    Гарантирует чистую БД для каждого теста.
    """
    # Для каждого теста пересоздаем таблицы, чтобы начать с чистого листа
    db_manager.recreate_tables(schema_file='schema_sqlite.sql')
    with app.test_client() as client:
        yield client