# app/utils.py
import logging
from flask import g
from mailersend import Email  # ИСПОЛЬЗУЕМ КЛАСС 'Email', как подсказывала ошибка
from app.config import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email_notification(recipients: list, subject_key: str, body_key: str, template_vars: dict = None):
    """
    Отправляет email-уведомление с использованием MailerSend.
    """
    if not isinstance(recipients, list):
        recipients = [recipients]

    try:
        # Получаем переведенные тему и тело письма
        subject = g.tr.get(subject_key, "Notification")
        html_body_template = g.tr.get(body_key, "")
        
        # Подставляем переменные в шаблон письма
        if template_vars:
            html_body = html_body_template.format(**template_vars)
        else:
            html_body = html_body_template

        # Инициализируем MailerSend
        mailer = Email(settings.MAILERSEND_API_TOKEN)

        # Определяем данные письма
        mail_from = {
            "email": settings.MAIL_FROM_EMAIL,
            "name": "Honest Reviews" 
        }
        recipients_list = [
            {"email": recipient} for recipient in recipients
        ]

        # Собираем все данные для отправки в один словарь
        mail_data = {
            "from": mail_from,
            "to": recipients_list,
            "subject": subject,
            "html": html_body,
            "text": "This is a fallback text for email clients that do not render HTML."
        }
        
        # Отправляем письмо
        mailer.send(mail_data)
        
        logger.info(f"Email sent successfully to {recipients} with subject '{subject}'")

    except Exception as e:
        logger.error(f"Failed to send email to {recipients}. Error: {e}")