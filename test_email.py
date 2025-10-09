# Файл: test_email.py
import os
from dotenv import load_dotenv
from mailersend import Email
import traceback

# 1. Загружаем переменные из .env файла
load_dotenv()
print("Загружаем переменные окружения из файла .env...")

# 2. Получаем API ключ и email отправителя
api_token = os.getenv("MAILERSEND_API_TOKEN")
from_email = os.getenv("MAIL_FROM_EMAIL")

if not api_token or not from_email:
    print("\nОШИБКА: Убедитесь, что в вашем .env файле есть MAILERSEND_API_TOKEN и MAIL_FROM_EMAIL!")
    exit()

print(f"Найден API ключ (первые 5 символов): SG..{api_token[-5:]}")
print(f"Email отправителя: {from_email}")

# 3. Настраиваем письмо
mailer = Email(api_token)

# !!! ВАЖНО: Укажите ВАШ реальный email, чтобы получить тестовое письмо !!!
test_recipient_email = "wowvideoko@gmail.com"

print(f"Попытка отправить письмо на: {test_recipient_email}\n")

mail_body = {
    "from": {
        "email": from_email,
        "name": "Локальный Тестовый Скрипт"
    },
    "to": [
        {"email": test_recipient_email}
    ],
    "subject": "Проверка MailerSend",
    "html": "<h1>Все работает!</h1><p>Если вы видите это письмо, значит, ваша локальная версия MailerSend и API ключ настроены правильно.</p>",
    "text": "Все работает! Если вы видите это письмо, значит, ваша локальная версия MailerSend и API ключ настроены правильно."
}

# 4. Пытаемся отправить
try:
    mailer.send(mail_body)
    print("✅ УСПЕХ! Письмо успешно отправлено. Проверьте ваш почтовый ящик.")
    print("Это доказывает, что ваша локальная версия mailersend и API ключ - РАБОЧИЕ.")

except Exception:
    print("❌ ОШИБКА! Не удалось отправить письмо.")
    print("Подробности ошибки ниже:")
    traceback.print_exc()