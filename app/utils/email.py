import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings
from app.utils.logger import logger


def send_email(to_email: str, subject: str, body: str, attachment_paths: list[str] | None = None) -> None:

    message = MIMEMultipart()
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    for path in (attachment_paths or []):

        if not path or not os.path.exists(path):

            continue

        with open(path, "rb") as file:

            part = MIMEBase("application", "octet-stream")
            part.set_payload(file.read())

        encoders.encode_base64(part)

        filename = os.path.basename(path)

        part.add_header("Content-Disposition", f"attachment; filename={filename}")

        message.attach(part)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:

        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(message)

    logger.info(f"Email sent to {to_email} : {subject}")