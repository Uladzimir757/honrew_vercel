# Файл: app/utils.py

import logging
from flask import g
from mailersend import MailerSend
from mailersend.helpers.mail import MailerMail, MailerRecipient
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email_notification(recipients: list, subject_key: str, body_key: str, template_vars: dict):
    """
    Отправляет email, используя API MailerSend (v2+).
    Всегда ожидает 'template_vars' в виде готового словаря.
    """
    if not settings.MAILERSEND_API_TOKEN:
        logger.error("MAILERSEND_API_TOKEN is not set. Cannot send email.")
        return

    if not isinstance(recipients, list):
        recipients = [recipients]

    try:
        mailer = MailerSend(settings.MAILERSEND_API_TOKEN)

        subject = g.tr.get(subject_key, "Notification")
        body_template = g.tr.get(body_key, "")
        html_body = body_template.format(**template_vars) if template_vars else body_template
        
        mailer_mail = MailerMail(
            from_email={
                "email": settings.MAIL_FROM_EMAIL,
                "name": "Honest Reviews"
            },
            to_recipients=[
                MailerRecipient(email=recipient) for recipient in recipients
            ],
            subject=subject,
            html_content=html_body,
            text_content="This is a plain text version of the email."
        )

        response = mailer.send(mailer_mail)
        logger.info(f"Email sent successfully to {recipients}. Response status: {response.status_code}")

    except Exception as e:
        logger.error(f"Failed to send email to {recipients} via MailerSend. Error: {e}")
        raise