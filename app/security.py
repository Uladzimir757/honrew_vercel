from passlib.context import CryptContext

# Используем pure-python алгоритм, совместимый с Cloudflare
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, соответствует ли обычный пароль хэшированному."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Создает хэш из обычного пароля."""
    return pwd_context.hash(password)