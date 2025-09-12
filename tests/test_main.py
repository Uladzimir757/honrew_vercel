import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_read_main(async_client: AsyncClient):
    """Тест: главная страница должна открываться успешно (код 200)."""
    response = await async_client.get("/")
    assert response.status_code == 200
    assert "Сила в правде" in response.text

@pytest.mark.asyncio
async def test_login_page_loads(async_client: AsyncClient):
    """Тест: страница входа должна открываться успешно (код 200)."""
    response = await async_client.get("/login")
    assert response.status_code == 200
    assert "Вход в аккаунт" in response.text

@pytest.mark.asyncio
async def test_profile_redirects_unauthenticated(async_client: AsyncClient):
    """Тест: неавторизованный пользователь должен быть перенаправлен со страницы профиля."""
    response = await async_client.get("/profile", follow_redirects=False)
    # Ожидаем код 303 See Other, который перенаправляет на страницу логина
    assert response.status_code == 303
    assert "/login" in response.headers["location"]

@pytest.mark.asyncio
async def test_profile_loads_authenticated(authenticated_client: AsyncClient):
    """Тест: авторизованный пользователь должен успешно загружать страницу профиля."""
    response = await authenticated_client.get("/profile")
    assert response.status_code == 200
    assert "Мой профиль" in response.text