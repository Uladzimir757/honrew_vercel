# Файл: app/routers/__init__.py

from .auth import auth_bp
from .pages import pages_bp
from .videos import videos_bp
from .users import users_bp
from .complaints import complaints_bp
from .admin import admin_bp

# Этот код собирает все blueprint'ы в одном месте,
# чтобы их можно было импортировать одной строкой.