# Файл: test_mailersend_v2.py
import os
from dotenv import load_dotenv
import traceback

# Правильные импорты для API v2.0.0
from mailersend import MailerSendClient
from mailersend.models.email import EmailContact, EmailRequest

# 1. Загружаем переменные из .env файла
load_dotenv()
print("Загружаем переменные окружения...")

# 2. Получаем API ключ и email отправителя
api_token = os.getenv("MAILERSEND_API_TOKEN")
from_email_address = os.getenv("MAIL_FROM") 

if not api_token or not from_email_address:
    print("\nОШИБКА: Убедитесь, что в .env файле есть MAILERSEND_API_TOKEN и MAIL_FROM!")
    exit()

print(f"Найден API ключ MailerSend...")
print(f"Email отправителя: {from_email_address}")

# 3. Настраиваем письмо, используя правильные Pydantic-объекты
try:
    mailer = MailerSendClient(api_token)

    # !!! ВАЖНО: Укажите ВАШ реальный email для получения тестового письма !!!
    test_recipient_email = "wowvideoko@gmail.com"
    print(f"Попытка отправить письмо на: {test_recipient_email}\n")

    # Создаем объекты, как того требует библиотека
    from_contact = EmailContact(email=from_email_address, name="Тест MailerSend v2")
    to_contacts = [EmailContact(email=test_recipient_email)]

    # Собираем главный Pydantic-объект EmailRequest
    email_request = EmailRequest(
        # --- ИСПРАВЛЕНО: 'from_contact' заменено на 'from_email' ---
        from_email=from_contact,
        to=to_contacts,
        subject="Финальный тест MailerSend v2.0.0",
        html="<h1>Ура!</h1><p>Если это письмо дошло, значит, мы победили.</p>",
        text="Все работает!"
    )

    # 4. Пытаемся отправить
    print("Пытаюсь отправить Pydantic-ОБЪЕКТ через MailerSendClient...")
    response = mailer.emails.send(email_request)
    print(f"✅ УСПЕХ! Письмо отправлено. Статус ответа сервера: {response.status_code}")

except Exception:
    print("❌ ОШИБКА! Не удалось отправить письмо.")
    print("Подробности ошибки ниже:")
    traceback.print_exc()