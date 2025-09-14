# Файл: manage.py
import os
import argparse
from app.main import get_app, PostgresManager
from app.config import settings

# Создаем "фейковый" экземпляр приложения Flask, чтобы получить доступ к его контексту.
# Это позволяет нам работать с базой данных так же, как в основном приложении.
app = get_app()

def delete_user(email: str):
    """
    Находит и удаляет пользователя по email, а также все его файлы из R2.
    """
    with app.app_context():
        db = PostgresManager(settings.DATABASE_URL)
        try:
            print(f"Ищем пользователя с email: {email}...")
            user_to_delete = db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))

            if not user_to_delete:
                print(f"Пользователь с email {email} не найден.")
                return

            user_id_to_delete = user_to_delete["id"]
            print(f"Найден пользователь с ID: {user_id_to_delete}. Начинаем удаление...")

            # 1. Удаляем файлы пользователя из R2 (если они есть)
            try:
                # Импортируем Boto3 только здесь, чтобы не требовать его для всего приложения
                import boto3
                session = boto3.session.Session()
                r2 = session.client(
                    's3',
                    endpoint_url=settings.R2_ENDPOINT_URL,
                    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                    region_name='auto'
                )
                
                print("Ищем файлы пользователя в R2...")
                user_videos = db.fetch_all("SELECT filename, preview_filename FROM videos WHERE user_id = %s", (user_id_to_delete,))
                for video in user_videos:
                    if video["filename"]:
                        print(f"  Удаляем файл: {video['filename']}")
                        r2.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=video['filename'])
                    if video["preview_filename"]:
                        print(f"  Удаляем превью: {video['preview_filename']}")
                        r2.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=video['preview_filename'])

                if user_to_delete["avatar_filename"]:
                    print(f"  Удаляем аватар: {user_to_delete['avatar_filename']}")
                    r2.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=user_to_delete['avatar_filename'])

            except Exception as e:
                print(f"Ошибка при удалении файлов пользователя {user_id_to_delete} из R2: {e}")
                print("Продолжаем удаление данных из базы...")

            # 2. Удаляем пользователя из базы данных (каскадное удаление позаботится об остальном)
            db.execute("DELETE FROM users WHERE id = %s", (user_id_to_delete,))
            print(f"Пользователь {email} и все его данные успешно удалены из базы.")

        finally:
            db.close()


def verify_user(email: str):
    """
    Принудительно верифицирует email пользователя.
    """
    with app.app_context():
        db = PostgresManager(settings.DATABASE_URL)
        try:
            print(f"Ищем пользователя с email: {email}...")
            user = db.fetch_one("SELECT id, is_verified FROM users WHERE email = %s", (email,))

            if not user:
                print(f"Пользователь с email {email} не найден.")
                return
            
            if user['is_verified']:
                print(f"Пользователь {email} уже верифицирован.")
                return

            db.execute("UPDATE users SET is_verified = TRUE, verification_token = NULL WHERE email = %s", (email,))
            print(f"Пользователь {email} успешно верифицирован.")

        finally:
            db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Управление пользователями HonestReviews.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Команда для удаления пользователя
    delete_parser = subparsers.add_parser("delete-user", help="Удалить пользователя по email.")
    delete_parser.add_argument("email", type=str, help="Email пользователя для удаления.")

    # Команда для верификации пользователя
    verify_parser = subparsers.add_parser("verify-user", help="Принудительно верифицировать пользователя по email.")
    verify_parser.add_argument("email", type=str, help="Email пользователя для верификации.")

    args = parser.parse_args()

    if args.command == "delete-user":
        delete_user(args.email)
    elif args.command == "verify-user":
        verify_user(args.email)