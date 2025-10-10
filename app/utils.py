# Файл: app/utils.py

import logging
from flask import g
from app.config import settings

# Правильные импорты для mailersend v2.0.0
from mailersend import MailerSendClient
from mailersend.models.email import EmailContact, EmailRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email_notification(recipients: list, subject_key: str, body_key: str, template_vars: dict):
    """
    Отправляет email, используя API MailerSend (v2.0.0).
    """
    if not settings.MAILERSEND_API_TOKEN:
        logger.error("MAILERSEND_API_TOKEN is not set. Cannot send email.")
        return

    if not isinstance(recipients, list):
        recipients = [recipients]

    try:
        # Инициализируем клиент
        mailer = MailerSendClient(settings.MAILERSEND_API_TOKEN)

        # Формируем тему и тело письма
        subject = g.tr.get(subject_key, "Notification")
        body_template = g.tr.get(body_key, "")
        html_body = body_template.format(**template_vars) if template_vars else body_template

        # Собираем Pydantic-объект для отправки
        from_contact = EmailContact(email=settings.MAIL_FROM, name="Honest Reviews")
        to_contacts = [EmailContact(email=recipient) for recipient in recipients]

        email_request = EmailRequest(
            from_email=from_contact,
            to=to_contacts,
            subject=subject,
            html=html_body,
            text="This is a plain text version of the email." # Запасной текстовый вариант
        )

        # Отправляем письмо
        response = mailer.emails.send(email_request)
        logger.info(f"Email sent successfully to {recipients}. Response status: {response.status_code}")

    except Exception as e:
        logger.error(f"Failed to send email to {recipients} via MailerSend. Error: {e}")
        raise