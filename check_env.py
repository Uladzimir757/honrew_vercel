# Файл: check_env.py
import os
from dotenv import load_dotenv

print("Пытаюсь загрузить .env файл...")
loaded = load_dotenv()

if loaded:
    print("✅ Файл .env найден и загружен!")
else:
    print("❌ ВНИМАНИЕ: Файл .env не найден в текущей папке!")

print("-" * 20)
print("Проверяю переменные:")

api_token = os.getenv("MAILERSEND_API_TOKEN")
from_email = os.getenv("MAIL_FROM")

if api_token:
    print(f"✅ MAILERSEND_API_TOKEN: Найден (последние 5 символов: ...{api_token[-5:]})")
else:
    print("❌ MAILERSEND_API_TOKEN: НЕ НАЙДЕН!")

if from_email:
    print(f"✅ MAIL_FROM: Найден ({from_email})")
else:
    print("❌ MAIL_FROM: НЕ НАЙДЕН!")

print("-" * 20)