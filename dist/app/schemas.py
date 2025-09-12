from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

# ДОБАВЛЕННЫЕ ИМПОРТЫ ДЛЯ МОДЕЛЕЙ БАЗЫ ДАННЫХ
import sqlalchemy
from .database import metadata

# --- Существующие Pydantic модели ---

class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    is_admin: bool
    is_verified: bool
    
    # ИЗМЕНЕНИЕ: Используем ConfigDict вместо class Config
    model_config = ConfigDict(from_attributes=True)

class Video(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: str
    filename: str
    user_id: int
    what: Optional[str] = None
    where: Optional[str] = None
    media_type: str
    created_at: datetime
    rating: Optional[int] = None

    # ИЗМЕНЕНИЕ: Используем ConfigDict вместо class Config
    model_config = ConfigDict(from_attributes=True)


# --- НОВЫЕ SQLAlchemy МОДЕЛИ ДЛЯ БАЗЫ ДАННЫХ ---

# Модель для лайков
likes = sqlalchemy.Table(
    "likes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sqlalchemy.Column("video_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.TIMESTAMP, server_default=sqlalchemy.func.now()),
    # Уникальное ограничение, чтобы один пользователь не мог лайкнуть видео дважды
    sqlalchemy.UniqueConstraint('user_id', 'video_id', name='unique_user_video_like')
)

# Модель для комментариев
comments = sqlalchemy.Table(
    "comments",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("content", sqlalchemy.Text, nullable=False),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sqlalchemy.Column("video_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.TIMESTAMP, server_default=sqlalchemy.func.now()),
    sqlalchemy.Column("updated_at", sqlalchemy.TIMESTAMP, server_default=sqlalchemy.func.now(), onupdate=sqlalchemy.func.now())
)