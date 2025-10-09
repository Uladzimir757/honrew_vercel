# Файл: app/utils.py

import logging
from flask import g
# Используем старый импорт
from mailersend import Email 
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email_notification(recipients: list, subject_key: str, body_key: str, template_vars: dict):
    """
    Отправляет email, используя API MailerSend (старая версия, v1.x.x).
    Всегда ожидает 'template_vars' в виде готового словаря.
    """
    if not settings.MAILERSEND_API_TOKEN:
        logger.error("MAILERSEND_API_TOKEN is not set. Cannot send email.")
        return

    if not isinstance(recipients, list):
        recipients = [recipients]

    try:
        # Старая инициализация клиента
        mailer = Email(settings.MAILERSEND_API_TOKEN)

        subject = g.tr.get(subject_key, "Notification")
        body_template = g.tr.get(body_key, "")
        
        # Код форматирования остается тем же, он работает со словарем
        html_body = body_template.format(**template_vars) if template_vars else body_template
        
        mail_from = {
            "email": settings.MAIL_FROM_EMAIL,
            "name": "Honest Reviews" 
        }
        
        recipients_list = [{"email": recipient} for recipient in recipients]

        # Старая версия библиотеки принимает на вход простой словарь
        mail_data = {
            "from": mail_from,
            "to": recipients_list,
            "subject": subject,
            "html": html_body,
            "text": "This is a plain text version of the email."
        }
        
        # Метод send() вызывается у объекта Email и принимает словарь
        mailer.send(mail_data)
        logger.info(f"Email sent successfully to {recipients} via MailerSend")

    except Exception as e:
        logger.error(f"Failed to send email to {recipients} via MailerSend. Error: {e}")
        raise