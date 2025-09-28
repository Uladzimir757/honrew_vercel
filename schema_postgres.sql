-- Схема базы данных для PostgreSQL (Продакшн)

DROP TABLE IF EXISTS company_replies;
DROP TABLE IF EXISTS complaints;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS likes;
DROP TABLE IF EXISTS videos;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    username TEXT UNIQUE,
    bio TEXT,
    avatar_filename TEXT,
    hashed_password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    verification_token TEXT,
    password_reset_token TEXT,
    password_reset_expires TIMESTAMPTZ,
    delete_token TEXT,
    delete_token_expires TIMESTAMPTZ,
    user_type TEXT DEFAULT 'client' NOT NULL
);

CREATE TABLE videos (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    filename TEXT NOT NULL,
    preview_filename TEXT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    what TEXT,
    "where" TEXT, -- "where" - ключевое слово, поэтому в кавычках
    media_type TEXT DEFAULT 'video',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    rating INTEGER,
    status TEXT DEFAULT 'pending_review' NOT NULL
);

CREATE TABLE likes (
    video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (video_id, user_id)
);

CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending_review' NOT NULL
);

CREATE TABLE complaints (
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL,
    content_type TEXT NOT NULL,
    reason TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending' NOT NULL
);

CREATE TABLE company_replies (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    video_id INTEGER NOT NULL UNIQUE REFERENCES videos(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);