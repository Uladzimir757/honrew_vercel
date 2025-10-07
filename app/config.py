# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Настройки базы данных
    DATABASE_URL: str
    
    # Настройки почты (MailerSend)
    MAILERSEND_API_TOKEN: str
    MAIL_FROM_EMAIL: str
    
    # Настройки безопасности
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Настройки S3/R2
    S3_ENDPOINT_URL: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str
    R2_PUBLIC_URL: str
    
    # Прочие настройки
    ITEMS_PER_PAGE: int = 12

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

settings = Settings()