from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    pass


def send_email(*, to_address: str, subject: str, body_text: str, reply_to: str | None = None) -> str:
    settings = get_settings()
    if not to_address:
        raise EmailDeliveryError("missing_recipient")

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to_address
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body_text)

    try:
        if settings.smtp_use_tls:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
            server.starttls()
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        refused = server.send_message(msg)
        server.quit()
    except smtplib.SMTPException as exc:
        logger.exception("SMTP send failed")
        raise EmailDeliveryError("smtp_failed") from exc

    if refused:
        raise EmailDeliveryError("smtp_refused")

    message_id = msg.get("Message-ID") or f"local-{abs(hash((to_address, subject, body_text)))}"
    return str(message_id).strip("<>")