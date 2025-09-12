# Файл: app/utils.py

import logging
import json
import requests  # Используем стандартную библиотеку requests вместо pyodide
from fastapi import Request
from app.config import settings # Предполагается, что у вас есть файл настроек

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Обновленная функция отправки Email через MailChannels ---
def send_email_notification(  # Функция теперь синхронная (убрали async)
    request: Request,
    recipients: list[str],
    subject_key: str,
    body_key: str,
    template_vars: dict = None
):
    """
    Отправляет email, используя API MailChannels через стандартные HTTP-запросы.
    Подходит для любого серверного окружения, включая Vercel.
    """
    from app.dependencies import get_language_and_translations
    
    # Получаем язык и переводы из запроса
    lang, tr = get_language_and_translations(request)
    
    subject = tr.get(subject_key, "Notification")
    body_template = tr.get(body_key, "")
    
    # Подставляем переменные в тело письма
    body = body_template.format(**template_vars) if template_vars else body_template

    # Формируем JSON-тело запроса по спецификации MailChannels
    # Структура тела запроса остается той же самой
    mailchannels_data = {
        "personalizations": [
            {
                "to": [{"email": email} for email in recipients]
            }
        ],
        "from": {
            # Email отправителя лучше брать из настроек, а не хардкодить
            "email": settings.MAIL_FROM_EMAIL, 
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
        # Совершаем HTTP POST запрос к API MailChannels с помощью requests
        response = requests.post(
            "https://api.mailchannels.net/tx/v1/send",
            headers={"Content-Type": "application/json"},
            json=mailchannels_data,  # requests сам преобразует dict в JSON
        )

        # Эта строка вызовет исключение, если код ответа не 2xx (например, 400, 500)
        response.raise_for_status()

        logger.info(f"Email успешно отправлен на {recipients}")

    except requests.exceptions.RequestException as e:
        # Логируем ошибки сети или HTTP-статуса
        logger.error(f"Ошибка отправки email через MailChannels: {e}")
        # Если есть ответ от сервера, логируем и его
        if e.response is not None:
            logger.error(f"Ответ сервера: {e.response.status_code} {e.response.text}")
            
    except Exception as e:
        logger.error(f"Критическая ошибка при отправке email: {e}")