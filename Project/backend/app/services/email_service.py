import logging
from email.message import EmailMessage

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str) -> None:
    if settings.EMAIL_MOCK:
        logger.info("EMAIL [mock] to=%s subject=%s\n%s", to, subject, body)
        return

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )


async def send_verification_email(email: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    await send_email(
        email,
        "Verify your SmartPrintX account",
        f"Welcome to SmartPrintX!\n\nClick to verify: {link}\n\nOr use token: {token}",
    )


async def send_password_reset_email(email: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    await send_email(
        email,
        "Reset your SmartPrintX password",
        f"Reset your password: {link}\n\nOr use token: {token}",
    )


async def send_order_notification(email: str, job_id: int, status: str, collection_code: str | None = None) -> None:
    body = f"Your print job #{job_id} is now: {status.upper()}"
    if collection_code and status == "completed":
        body += f"\n\nCollection code: {collection_code}"
    await send_email(email, f"Print Job #{job_id} - {status.title()}", body)
