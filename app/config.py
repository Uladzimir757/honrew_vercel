import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    
    # --- НАСТРОЙКИ S3/R2 ---
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_ENDPOINT_URL: str
    S3_BUCKET_NAME: str
    R2_PUBLIC_URL: str # <-- НОВАЯ ПЕРЕМЕННАЯ
    # -----------------------

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    
    ITEMS_PER_PAGE: int = 9
    MAX_FILE_SIZE: int = 52428800  # 50 MB
    MAX_UPLOADS_PER_HOUR: int = 5
    UPLOAD_TIMEFRAME_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()