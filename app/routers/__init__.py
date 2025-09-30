# Файл: app/routers/__init__.py

from .auth import auth_bp
from .pages import pages_bp
from .reviews import reviews_bp  # <-- ИЗМЕНЕНИЕ: было .videos import videos_bp
from .users import users_bp
from .complaints import complaints_bp
from .admin import admin_bp
from .categories import categories_bp

__all__ = [
    "auth_bp",
    "pages_bp",
    "reviews_bp",
    "users_bp",
    "complaints_bp",
    "admin_bp",
    "categories_bp",
]