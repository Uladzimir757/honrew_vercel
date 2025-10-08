# Файл: app/utils.py

import logging
from flask import g
from mailersend import Email
from app.config import settings

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def send_email_notification(recipients: list, subject_key: str, body_key: str, template_vars=None):
    """
    Отправляет email, используя API MailerSend.
    Принимает 'template_vars' как Pydantic-модель или словарь.
    """
    if not settings.MAILERSEND_API_TOKEN:
        logger.error("MAILERSEND_API_TOKEN is not set. Cannot send email.")
        return

    if not isinstance(recipients, list):
        recipients = [recipients]

    try:
        subject = g.tr.get(subject_key, "Notification")
        body_template = g.tr.get(body_key, "")
        
        # 'Умная' проверка: преобразуем в словарь, только если это Pydantic-объект
        vars_dict = {}
        if template_vars:
            if hasattr(template_vars, 'model_dump'):
                vars_dict = template_vars.model_dump()
            elif isinstance(template_vars, dict):
                vars_dict = template_vars
        
        html_body = body_template.format(**vars_dict) if vars_dict else body_template

        mailer = Email(settings.MAILERSEND_API_TOKEN)

        mail_from = {
            "email": settings.MAIL_FROM_EMAIL,
            "name": "Honest Reviews" 
        }
        
        recipients_list = [{"email": recipient} for recipient in recipients]

        mail_data = {
            "from": mail_from,
            "to": recipients_list,
            "subject": subject,
            "html": html_body,
            "text": "This is a plain text version of the email."
        }
        
        mailer.send(mail_data)
        logger.info(f"Email sent successfully to {recipients} via MailerSend")

    except Exception as e:
        logger.error(f"Failed to send email to {recipients} via MailerSend. Error: {e}")
        # В реальном приложении можно добавить более детальную обработку ошибок
        raise