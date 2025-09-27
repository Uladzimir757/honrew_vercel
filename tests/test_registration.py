# Файл: tests/test_registration.py
import pytest
from app.database import db_manager

def test_successful_registration(client):
    """Тест: Успешная регистрация нового пользователя."""
    new_user_data = {
        "email": "newuser@example.com",
        "password": "Password123",
        "confirm_password": "Password123",
        "user_type": "client",
        "consent": "on"
    }
    response = client.post("/register", data=new_user_data, follow_redirects=False)
    
    # ПРОВЕРКА 1: Успешная регистрация должна перенаправлять на страницу входа
    assert response.status_code == 302
    assert "/login" in response.headers.get("location", "")

    # ПРОВЕРКА 2: Пользователь должен появиться в базе данных
    user_in_db = db_manager.fetch_one("SELECT * FROM users WHERE email = ?", ("newuser@example.com",))
    assert user_in_db is not None

def test_registration_with_existing_email(client):
    """Тест: Попытка регистрации с уже существующим email."""
    # Создаем пользователя, чтобы email был занят
    db_manager.execute_query(
        "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
        ("existing@example.com", "somehashedpassword")
    )
    
    response = client.post("/register", data={
        "email": "existing@example.com",
        "password": "Password123",
        "confirm_password": "Password123",
        "user_type": "client",
        "consent": "on"
    }, follow_redirects=False)
    
    # ИЗМЕНЕНИЕ: Теперь мы проверяем, что при ошибке происходит редирект обратно на страницу регистрации
    assert response.status_code == 302
    assert "/register" in response.headers.get("location", "")

def test_registration_with_mismatched_passwords(client):
    """Тест: Попытка регистрации с несовпадающими паролями."""
    response = client.post("/register", data={
        "email": "anotheruser@example.com",
        "password": "Password123",
        "confirm_password": "Password456",
        "user_type": "client",
        "consent": "on"
    }, follow_redirects=False)
    
    # ИЗМЕНЕНИЕ: Здесь также проверяем редирект обратно на страницу регистрации
    assert response.status_code == 302
    assert "/register" in response.headers.get("location", "")