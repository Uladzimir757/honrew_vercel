# app/utils.py
import logging
from flask import g
from mailersend import emails
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
        mailer = emails.NewEmail(settings.MAILERSEND_API_TOKEN)

        # Определяем данные письма
        mail_body = {}
        mail_from = {
            "email": settings.MAIL_FROM_EMAIL,
            "name": "Honest Reviews" 
        }
        recipients_list = [
            {"email": recipient} for recipient in recipients
        ]

        # Устанавливаем параметры
        mailer.set_mail_from(mail_from, mail_body)
        mailer.set_mail_to(recipients_list, mail_body)
        mailer.set_subject(subject, mail_body)
        mailer.set_html_content(html_body, mail_body)
        
        # Отправляем письмо
        mailer.send(mail_body)
        
        logger.info(f"Email sent successfully to {recipients} with subject '{subject}'")

    except Exception as e:
        logger.error(f"Failed to send email to {recipients}. Error: {e}")