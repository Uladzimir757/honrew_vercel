# Файл: app/utils.py

import logging
import json
from fastapi import Request

# pyodide-http - это специальная библиотека для совершения HTTP-запросов изнутри воркера
import pyodide.http

# --- Настройка логирования ---
# Логи будут выводиться в консоль wrangler'а, что идеально для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Новая функция отправки Email через MailChannels ---
async def send_email_notification(
    request: Request,
    recipients: list[str],
    subject_key: str,
    body_key: str,
    template_vars: dict = None
):
    """
    Отправляет email, используя встроенную интеграцию Cloudflare с MailChannels.
    Не требует настроек SMTP или ключей API.
    """
    from app.dependencies import get_language_and_translations
    
    # Получаем язык и переводы из запроса
    lang, tr = get_language_and_translations(request)
    
    subject = tr.get(subject_key, "Notification")
    body_template = tr.get(body_key, "")
    
    # Подставляем переменные в тело письма
    body = body_template.format(**template_vars) if template_vars else body_template

    # Формируем JSON-тело запроса по спецификации MailChannels
    mailchannels_data = {
        "personalizations": [
            {
                "to": [{"email": email} for email in recipients]
            }
        ],
        "from": {
            # Убедитесь, что этот email совпадает с тем, что в ваших DNS записях для MailChannels
            "email": "no-reply@yourdomain.com", 
            "name": "Honest Reviews"
        },
        "subject": subject,
        "content": [
            {
                "type": "text/html",
                "value": body
            }
        ]
    }

    try:
        # Совершаем HTTP POST запрос к API MailChannels
        response = await pyodide.http.pyfetch(
            "https://api.mailchannels.net/tx/v1/send",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(mailchannels_data),
        )

        # Проверяем статус ответа
        if 200 <= response.status < 300:
            logger.info(f"Email успешно отправлен на {recipients}")
        else:
            response_text = await response.string()
            logger.error(f"Ошибка отправки email: {response.status} {response_text}")

    except Exception as e:
        logger.error(f"Критическая ошибка при отправке email: {e}")