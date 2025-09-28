# tests/test_main.py
import pytest
from flask import url_for, session

def test_index_loads_successfully(client):
    """Тест: Главная страница загружается успешно."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome" in response.data # Или любой другой текст с главной страницы

def test_profile_redirects_unauthenticated(client):
    """Тест: неавторизованный пользователь должен быть перенаправлен со страницы профиля."""
    response = client.get("/profile", follow_redirects=False)
    assert response.status_code == 302
    assert "Location" in response.headers
    # Убедитесь, что URL перенаправления соответствует вашему роуту логина
    assert url_for('auth.handle_login') in response.headers['Location']

def test_profile_loads_authenticated(authenticated_client): # Использование новой фикстуры
    """Тест: Авторизованный пользователь должен успешно загружать страницу профиля."""
    response = authenticated_client.get("/profile", follow_redirects=True)
    assert response.status_code == 200
    assert b"User Profile" in response.data # Или любой текст с вашей страницы профиля
    assert b"authenticated@example.com" in response.data # Проверить, что email пользователя отображается