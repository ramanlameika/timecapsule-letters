"""Email sending abstraction.

In development mode (ENVIRONMENT=dev or no SMTP host configured) emails are
printed to the application logs instead of being sent via SMTP.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body_text: str) -> None:
    """Send an email to *to*.

    Falls back to log-only mode when SMTP is not configured or when
    ``ENVIRONMENT=dev``.
    """
    if settings.environment == "dev" or not settings.smtp_host:
        _log_email(to, subject, body_text)
        return

    _send_via_smtp(to, subject, body_text)


def _log_email(to: str, subject: str, body_text: str) -> None:
    logger.info(
        "[DEV EMAIL] To: %s | Subject: %s\n%s",
        to,
        subject,
        body_text,
    )


def _send_via_smtp(to: str, subject: str, body_text: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg.attach(MIMEText(body_text, "plain"))

    smtp_cls = smtplib.SMTP_SSL if settings.smtp_tls else smtplib.SMTP
    with smtp_cls(settings.smtp_host, settings.smtp_port) as server:  # type: ignore[operator]
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from, [to], msg.as_string())
        logger.info("Email sent to %s (subject: %s)", to, subject)
