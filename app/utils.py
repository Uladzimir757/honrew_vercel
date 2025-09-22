# Файл: app/utils.py

import logging
import json
import requests
import boto3
import traceback
from botocore.exceptions import BotoCoreError, ClientError
from flask import Request
from app.config import settings

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Email sending function via MailChannels ---
def send_email_notification(
    request: Request,
    recipients: list[str],
    subject_key: str,
    body_key: str,
    template_vars: dict = None
):
    """
    Sends an email using the MailChannels API via standard HTTP requests.
    """
    from app.dependencies import get_language_and_translations
    
    lang, tr = get_language_and_translations(request)
    subject = tr.get(subject_key, "Notification")
    body_template = tr.get(body_key, "")
    body = body_template.format(**template_vars) if template_vars else body_template

    mailchannels_data = {
        "personalizations": [{"to": [{"email": email} for email in recipients]}],
        "from": {"email": settings.MAIL_FROM_EMAIL, "name": "Honest Reviews"},
        "subject": subject,
        "content": [{"type": "text/html", "value": body}]
    }

    try:
        response = requests.post(
            "https://api.mailchannels.net/tx/v1/send",
            headers={"Content-Type": "application/json"},
            json=mailchannels_data,
        )
        response.raise_for_status()
        logger.info(f"Email successfully sent to {recipients}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending email via MailChannels: {e}")
        if e.response is not None:
            logger.error(f"Server Response: {e.response.status_code} {e.response.text}")
    except Exception as e:
        logger.error(f"Critical error while sending email: {e}")


# --- R2 file upload function with detailed logging ---
def upload_file_to_r2(file_obj, object_name: str) -> bool:
    """
    Uploads a file-like object to a Cloudflare R2 bucket.
    """
    try:
        s3_client = boto3.client(
            service_name='s3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name='auto',
        )
    except Exception as e:
        logger.error(f"Critical error creating S3 client: {e}")
        traceback.print_exc()
        return False

    try:
        s3_client.upload_fileobj(
            file_obj,
            settings.S3_BUCKET_NAME,
            object_name
        )
        logger.info(f"File {object_name} successfully uploaded to bucket {settings.S3_BUCKET_NAME}.")
        return True
    except (BotoCoreError, ClientError) as e:
        logger.error(f"DETAILED R2 UPLOAD ERROR: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        logger.error(f"Unexpected error during R2 file upload: {e}")
        traceback.print_exc()
        return False