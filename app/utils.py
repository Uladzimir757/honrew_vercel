# Файл: app/utils.py

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import g
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email_notification(recipients: list, subject_key: str, body_key: str, template_vars: dict):
    """
    Отправляет email напрямую через SMTP, используя встроенные библиотеки Python.
    """
    if not all([settings.SMTP_SERVER, settings.SMTP_PORT, settings.SMTP_USERNAME, settings.SMTP_PASSWORD]):
        logger.error("SMTP settings are not configured. Cannot send email.")
        return

    if not isinstance(recipients, list):
        recipients = [recipients]

    try:
        subject = g.tr.get(subject_key, "Notification")
        body_template = g.tr.get(body_key, "")
        html_body = body_template.format(**template_vars) if template_vars else body_template

        # Создание сообщения
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.MAIL_FROM_EMAIL
        message["To"] = ", ".join(recipients)
        
        # Прикрепляем HTML-версию
        part = MIMEText(html_body, "html")
        message.attach(part)

        # Подключение к серверу и отправка
        # Используем SMTP_SSL для безопасного соединения с самого начала
        with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(
                settings.MAIL_FROM_EMAIL,
                recipients,
                message.as_string()
            )
        
        logger.info(f"Email sent successfully to {recipients} via SMTP.")

    except Exception as e:
        logger.error(f"Failed to send email via SMTP. Error: {e}")
        # В реальном приложении можно добавить более детальную обработку ошибок
        raise