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
    Отправляет email напрямую через SMTP, используя переменные с префиксом MAIL_
    """
    # Проверяем наличие новых переменных
    if not all([settings.MAIL_SERVER, settings.MAIL_PORT, settings.MAIL_USERNAME, settings.MAIL_PASSWORD]):
        logger.error("SMTP settings (MAIL_...) are not configured. Cannot send email.")
        return

    if not isinstance(recipients, list):
        recipients = [recipients]

    try:
        subject = g.tr.get(subject_key, "Notification")
        body_template = g.tr.get(body_key, "")
        html_body = body_template.format(**template_vars) if template_vars else html_body

        # Создание сообщения
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        # Используем MAIL_FROM вместо MAIL_FROM_EMAIL
        message["From"] = settings.MAIL_FROM
        message["To"] = ", ".join(recipients)

        part = MIMEText(html_body, "html")
        message.attach(part)

        # Подключение к серверу и отправка
        # Используем ваши переменные
        with smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(
                settings.MAIL_FROM,
                recipients,
                message.as_string()
            )

        logger.info(f"Email sent successfully to {recipients} via SMTP.")

    except Exception as e:
        logger.error(f"Failed to send email via SMTP. Error: {e}")
        raise