# Файл: app/config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    
    # --- Настройки S3/R2 ---
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_ENDPOINT_URL: str
    S3_BUCKET_NAME: str
    R2_PUBLIC_URL: str
    
    # --- Настройки почты (SendGrid) ---
    MAIL_FROM_EMAIL: str 
    SENDGRID_API_KEY: str  # <-- ДОБАВЛЕНО

    # --- Общие настройки ---
    ITEMS_PER_PAGE: int = 9
    MAX_FILE_SIZE: int = 52428800  # 50 MB
    MAX_UPLOADS_PER_HOUR: int = 5
    UPLOAD_TIMEFRAME_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()