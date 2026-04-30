"""Celery application and background tasks."""

import logging
from datetime import datetime, timezone

from celery import Celery
from celery.schedules import crontab

from app.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "timecapsule",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "deliver-due-letters-every-minute": {
            "task": "app.tasks.deliver_due_letters",
            "schedule": crontab(minute="*"),
        }
    },
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def deliver_due_letters(self) -> None:  # type: ignore[override]
    """Find all scheduled letters whose delivery time has passed and send them."""
    # Import here to avoid circular imports at module load time
    from app.crypto import decrypt_body
    from app.db import SessionLocal
    from app.email import send_email
    from app.models import Letter

    db = SessionLocal()
    try:
        now = datetime.now(tz=timezone.utc)
        due_letters = (
            db.query(Letter)
            .filter(Letter.status == "scheduled", Letter.deliver_at <= now)
            .all()
        )

        logger.info("Delivery sweep: found %d due letter(s)", len(due_letters))

        for letter in due_letters:
            try:
                body = decrypt_body(letter.encrypted_body)
                subject = letter.subject or "A letter from your past self"
                send_email(to=letter.email_to, subject=subject, body_text=body)

                letter.status = "sent"
                letter.sent_at = datetime.now(tz=timezone.utc)
                letter.error_message = None
                db.commit()
                logger.info("Letter %s delivered to %s", letter.id, letter.email_to)

            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to deliver letter %s: %s", letter.id, exc)
                letter.status = "failed"
                letter.error_message = str(exc)
                db.commit()
                # Retry the whole task after a delay so transient failures recover
                try:
                    raise self.retry(exc=exc)
                except self.MaxRetriesExceededError:
                    logger.error(
                        "Letter %s exceeded max retries and is marked failed.", letter.id
                    )
    finally:
        db.close()
