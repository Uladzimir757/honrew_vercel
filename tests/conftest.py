# tests/conftest.py (ПОЛНОСТЬЮ ЗАМЕНИТЕ НА ЭТО)
import pytest
from app.main import app as flask_app
from app.database import db_manager, DatabaseManager # Импортируем сам класс DatabaseManager
from flask import g, session
import os
import json # Для загрузки тестовых переводов

# Глобальная переменная для хранения оригинального db_manager (загружается один раз)
_original_db_manager_instance = None

@pytest.fixture(scope='session', autouse=True)
def setup_original_db_manager_reference():
    """Сохраняет ссылку на оригинальный db_manager, который инициализируется при первом импорте app.main."""
    global _original_db_manager_instance
    if _original_db_manager_instance is None:
        _original_db_manager_instance = db_manager # Сохраняем ссылку на глобальный экземпляр

@pytest.fixture(scope='session')
def app(setup_original_db_manager_reference):
    """
    Фикстура, которая создает экземпляр приложения для всей сессии тестов.
    Настраивает тестовую БД и подменяет глобальный db_manager.
    """
    # Сохраняем оригинальные значения для восстановления
    # Это не нужно, так как _original_db_manager_instance уже хранит ссылку
    # original_db_manager_url = _original_db_manager_instance.database_url 

    # Создаем новую конфигурацию для тестового приложения
    flask_app.config.from_mapping(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test_secret_key' # Для работы сессий
    )

    # Инициализируем **временный** DatabaseManager для тестов с SQLite
    test_db_url = 'sqlite:///./test.db'
    test_db_manager = DatabaseManager(test_db_url)
    
    # === ВАЖНОЕ ИЗМЕНЕНИЕ: Подменяем глобальный экземпляр db_manager ===
    # Мы напрямую изменяем объект, на который ссылается db_manager в модуле app.database
    # Это гарантирует, что все части приложения, которые импортируют db_manager,
    # будут использовать этот тестовый экземпляр.
    # Для этого мы модифицируем поля существующего _original_db_manager_instance
    _original_db_manager_instance.database_url = test_db_url
    _original_db_manager_instance.db_type = test_db_manager.db_type
    _original_db_manager_instance.param_style = test_db_manager.param_style
    _original_db_manager_instance.connection_args = test_db_manager.connection_args
    _original_db_manager_instance.connection = None # Сбрасываем соединение, чтобы оно пересоздалось

    # Создаем таблицы в тестовой БД, используя схему для SQLite
    _original_db_manager_instance.recreate_tables(schema_file='schema_sqlite.sql')

    yield flask_app # Передаем экземпляр Flask приложения тестам

    # === ВОССТАНАВЛИВАЕМ ОРИГИНАЛЬНЫЙ db_manager после завершения всех тестов ===
    _original_db_manager_instance.close_connection() # Закрываем соединение тестовой БД

    # Если вы хотите полностью восстановить _original_db_manager_instance до его первоначального состояния,
    # это будет сложнее, так как _original_db_manager_instance - это уже инициализированный объект.
    # Проще всего просто удалить тестовый файл БД и не беспокоиться о состоянии _original_db_manager_instance
    # после тестов, так как Flask приложение уже не работает.
    # Если Flask приложение будет запущено снова в той же сессии python,
    # ему придется заново инициализировать db_manager с правильным URL.
    # Для prod среды это не проблема, т.к. она запускается отдельно.

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
    _original_db_manager_instance.recreate_tables(schema_file='schema_sqlite.sql')
    with app.test_client() as client:
        with app.app_context():
            # Загружаем тестовые переводы для g.tr
            g.tr = load_test_translations()
        yield client

# Добавляем фикстуру для авторизованного клиента
@pytest.fixture(scope='function')
def authenticated_client(client):
    """
    Фикстура для клиента, который уже прошел аутентификацию.
    """
    with client:
        # 1. Зарегистрировать тестового пользователя
        test_email = "authenticated@example.com"
        test_password = "Password123"
        
        # Используем глобальный db_manager, который теперь указывает на тестовую SQLite
        param_ph = "?" if _original_db_manager_instance.param_style == 'qmark' else "%s"
        hashed_password = "test_hashed_password" # Или используйте вашу функцию get_password_hash
        _original_db_manager_instance.execute_query(
            f"INSERT INTO users (email, hashed_password, is_verified) VALUES ({param_ph}, {param_ph}, {param_ph})",
            (test_email, hashed_password, True)
        )
        
        # 2. Войти под этим пользователем
        client.post("/login", data={"email": test_email, "password": test_password}, follow_redirects=True)
        
        yield client

# Функция для загрузки тестовых переводов
def load_test_translations():
    """Загружает минимальный набор переводов для тестов."""
    return {
        "error_login_required": "Для доступа к этой странице требуется вход.",
        "error_consent_required": "Для регистрации необходимо согласиться с условиями.",
        "error_passwords_mismatch": "Пароли не совпадают.",
        "error_password_too_weak": "Пароль слишком слабый. Он должен быть не менее 8 символов, содержать хотя бы одну цифру и одну заглавную букву.",
        "error_user_exists": "Пользователь с таким email уже зарегистрирован.",
        "registration_check_email": "Вы успешно зарегистрированы. Пожалуйста, проверьте свою почту для подтверждения.",
        "error_login_failed": "Неверный email или пароль.",
        "error_not_verified": "Ваш аккаунт не подтвержден. Пожалуйста, проверьте почту.",
        "login_success_message": "Вы успешно вошли!",
        "error_access_denied": "Доступ запрещен. У вас нет прав администратора."
        # Добавьте сюда другие ключи, которые используются в вашем коде и могут вызвать KeyError
    }