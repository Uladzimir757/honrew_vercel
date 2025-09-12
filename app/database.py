import databases
import sqlalchemy
from .config import settings

database = databases.Database(settings.DATABASE_URL)
metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table(
    "users", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String, unique=True, nullable=False),
    sqlalchemy.Column("username", sqlalchemy.String, unique=True),
    sqlalchemy.Column("bio", sqlalchemy.Text),
    sqlalchemy.Column("avatar_filename", sqlalchemy.String),
    sqlalchemy.Column("hashed_password", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("is_admin", sqlalchemy.Boolean, default=False, nullable=False),
    sqlalchemy.Column("is_verified", sqlalchemy.Boolean, default=False, nullable=False),
    sqlalchemy.Column("verification_token", sqlalchemy.String),
    sqlalchemy.Column("password_reset_token", sqlalchemy.String),
    sqlalchemy.Column("password_reset_expires", sqlalchemy.TIMESTAMP),
    sqlalchemy.Column("delete_token", sqlalchemy.String),
    sqlalchemy.Column("delete_token_expires", sqlalchemy.TIMESTAMP),
    sqlalchemy.Column("user_type", sqlalchemy.String, default='client', nullable=False)
)

videos = sqlalchemy.Table(
    "videos", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("title", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("description", sqlalchemy.Text),
    sqlalchemy.Column("category", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("filename", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("preview_filename", sqlalchemy.String),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sqlalchemy.Column("what", sqlalchemy.String),
    sqlalchemy.Column("where", sqlalchemy.String),
    sqlalchemy.Column("media_type", sqlalchemy.String, default='video'),
    sqlalchemy.Column("created_at", sqlalchemy.TIMESTAMP, server_default=sqlalchemy.func.now()),
    sqlalchemy.Column("rating", sqlalchemy.Integer),
    sqlalchemy.Column("status", sqlalchemy.String, default='pending_review', nullable=False)
)

likes = sqlalchemy.Table(
    "likes", metadata,
    sqlalchemy.Column("video_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sqlalchemy.PrimaryKeyConstraint("video_id", "user_id"),
)

comments = sqlalchemy.Table(
    "comments", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("content", sqlalchemy.Text, nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.TIMESTAMP, server_default=sqlalchemy.func.now()),
    sqlalchemy.Column("video_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sqlalchemy.Column("status", sqlalchemy.String, default='pending_review', nullable=False)
)

complaints = sqlalchemy.Table(
    "complaints", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("content_id", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("content_type", sqlalchemy.String, nullable=False), # 'review' или 'comment'
    sqlalchemy.Column("reason", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id", ondelete="SET NULL")),
    sqlalchemy.Column("created_at", sqlalchemy.TIMESTAMP, server_default=sqlalchemy.func.now()),
    sqlalchemy.Column("status", sqlalchemy.String, default='pending', nullable=False) # 'pending' или 'resolved'
)

# --- НОВАЯ ТАБЛИЦА ДЛЯ ОТВЕТОВ КОМПАНИЙ ---
company_replies = sqlalchemy.Table(
    "company_replies", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("content", sqlalchemy.Text, nullable=False),
    sqlalchemy.Column("video_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("videos.id", ondelete="CASCADE"), unique=True, nullable=False),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.TIMESTAMP, server_default=sqlalchemy.func.now()),
    sqlalchemy.Column("updated_at", sqlalchemy.TIMESTAMP, server_default=sqlalchemy.func.now(), onupdate=sqlalchemy.func.now())
)