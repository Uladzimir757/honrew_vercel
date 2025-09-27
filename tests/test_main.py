import pytest

def test_read_main(client):
    """Тест: главная страница должна открываться успешно (код 200)."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Сила в правде" in response.data.decode('utf-8')

def test_login_page_loads(client):
    """Тест: страница входа должна открываться успешно (код 200)."""
    response = client.get("/login")
    assert response.status_code == 200
    assert "Вход в аккаунт" in response.data.decode('utf-8')

def test_profile_redirects_unauthenticated(client):
    """Тест: неавторизованный пользователь должен быть перенаправлен со страницы профиля."""
    response = client.get("/profile", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]

def test_profile_loads_authenticated(authenticated_client):
    """Тест: авторизованный пользователь должен успешно загружать страницу профиля."""
    response = authenticated_client.get("/profile")
    assert response.status_code == 200
    assert "Мой профиль" in response.data.decode('utf-8')