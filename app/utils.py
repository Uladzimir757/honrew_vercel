# app/utils.py
import logging
from flask import g
from mailersend import Email
from app.config import settings
from pydantic import BaseModel

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email_notification(recipients: list, subject_key: str, body_key: str, template_vars: BaseModel = None):
    """
    Отправляет email-уведомление с использованием MailerSend.
    """
    if not isinstance(recipients, list):
        recipients = [recipients]

    try:
        subject = g.tr.get(subject_key, "Notification")
        html_body_template = g.tr.get(body_key, "")
        
        # --- ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ---
        if template_vars:
            # Преобразуем Pydantic-объект в словарь перед форматированием
            html_body = html_body_template.format(**template_vars.model_dump())
        else:
            html_body = html_body_template
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

        mailer = Email(settings.MAILERSEND_API_TOKEN)

        mail_from = {
            "email": settings.MAIL_FROM_EMAIL,
            "name": "Honest Reviews" 
        }
        recipients_list = [
            {"email": recipient} for recipient in recipients
        ]

        mail_data = {
            "from": mail_from,
            "to": recipients_list,
            "subject": subject,
            "html": html_body,
            "text": "This is a fallback text for email clients that do not render HTML."
        }
        
        mailer.send(mail_data)
        
        logger.info(f"Email sent successfully to {recipients} with subject '{subject}'")

    except Exception as e:
        logger.error(f"Failed to send email to {recipients}. Error: {e}")
        # Передаем исключение дальше, чтобы его поймал вызывающий код
        raise