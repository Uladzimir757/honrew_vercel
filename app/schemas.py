# app/schemas.py

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

# --- ИСПРАВЛЕНИЕ ---
# 1. Убираем неверный импорт из database.py
# 2. Создаем объект MetaData прямо здесь
import sqlalchemy
metadata = sqlalchemy.MetaData()
# --- КОНЕЦ ИСПРАВЛЕНИЯ ---


# --- Модели для email-уведомлений (добавлены ранее) ---

class NewLikeEmailParams(BaseModel):
    liker_email: str
    review_title: str
    review_link: str

class NewCommentEmailParams(BaseModel):
    commenter_email: str
    review_title: str
    comment_content: str
    review_link: str


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

    model_config = ConfigDict(from_attributes=True)


# --- SQLAlchemy МОДЕЛИ (теперь они должны работать) ---

# Модель для лайков
likes = sqlalchemy.Table(
    "likes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sqlalchemy.Column("video_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.TIMESTAMP, server_default=sqlalchemy.func.now()),
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