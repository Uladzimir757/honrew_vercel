# app/config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Базы данных
    PROD_DATABASE_URL: str
    PREVIEW_DATABASE_URL: str
    
    # Настройки почты (MailerSend)
    MAILERSEND_API_TOKEN: str
    MAIL_FROM: str  # ИЗМЕНЕНО: Используем MAIL_FROM, как в ваших настройках Vercel
    
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

    @property
    def DATABASE_URL(self) -> str:
        if os.getenv('VERCEL_ENV') == 'production':
            return self.PROD_DATABASE_URL
        else:
            return self.PREVIEW_DATABASE_URL

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()