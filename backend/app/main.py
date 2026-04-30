"""FastAPI application entry point."""

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.crypto import encrypt_body
from app.db import get_db
from app.mailer import send_email
from app.models import Letter
from app.schemas import LetterCreate, LetterCreateResponse, VerifyResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TimeCapsule Letters",
    description="Write a letter today, receive it in the future.",
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/healthz", tags=["meta"])
def healthz() -> dict:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Create a letter
# ---------------------------------------------------------------------------


@app.post("/letters", response_model=LetterCreateResponse, status_code=201, tags=["letters"])
def create_letter(payload: LetterCreate, db: Session = Depends(get_db)) -> LetterCreateResponse:
    """
    Create a new future letter.

    The letter body is encrypted before storage. A verification token is
    generated, hashed, and the plain token is emailed to the recipient so
    they can confirm ownership before the letter is scheduled for delivery.
    """
    # Generate a secure random token (never stored in plaintext)
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    encrypted = encrypt_body(payload.body)

    letter = Letter(
        id=uuid.uuid4(),
        email_to=str(payload.email_to),
        subject=payload.subject,
        encrypted_body=encrypted,
        deliver_at=payload.deliver_at,
        status="pending_verification",
        verify_token_hash=token_hash,
    )
    db.add(letter)
    db.commit()
    db.refresh(letter)

    # Build verification link and send email
    verify_url = f"{settings.base_url}/letters/verify?token={raw_token}&letter_id={letter.id}"
    send_email(
        to=str(payload.email_to),
        subject="Verify your TimeCapsule letter",
        body_text=(
            f"Hi,\n\n"
            f"Please verify your email address to schedule your letter for delivery on "
            f"{payload.deliver_at.strftime('%Y-%m-%d %H:%M UTC')}.\n\n"
            f"Verification link (valid once):\n{verify_url}\n\n"
            f"If you did not create this letter, you can safely ignore this email.\n\n"
            f"— TimeCapsule Letters"
        ),
    )

    logger.info("Created letter %s for %s", letter.id, letter.email_to)
    return LetterCreateResponse(
        letter_id=letter.id,
        message=(
            "Letter created. Check your inbox for a verification link. "
            "Once verified your letter will be delivered on the chosen date."
        ),
    )


# ---------------------------------------------------------------------------
# Verify email / token
# ---------------------------------------------------------------------------


@app.get("/letters/verify", response_model=VerifyResponse, tags=["letters"])
def verify_letter(
    token: str = Query(..., description="Verification token from the email link"),
    letter_id: uuid.UUID = Query(..., description="Letter ID from the email link"),
    db: Session = Depends(get_db),
) -> VerifyResponse:
    """
    Verify the email address for a letter.

    Validates the token, marks the letter as ``scheduled``, and records
    the verification timestamp.
    """
    letter = db.get(Letter, letter_id)
    if letter is None:
        raise HTTPException(status_code=404, detail="Letter not found")

    if letter.status != "pending_verification":
        raise HTTPException(
            status_code=409,
            detail="Letter has already been verified or is in an unexpected state.",
        )

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    if letter.verify_token_hash != token_hash:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    letter.status = "scheduled"
    letter.verified_at = datetime.now(tz=timezone.utc)
    # Clear the token hash so it cannot be reused
    letter.verify_token_hash = None
    db.commit()

    logger.info("Letter %s verified and scheduled for %s", letter.id, letter.deliver_at)
    return VerifyResponse(
        message=(
            f"Email verified! Your letter is now scheduled for delivery on "
            f"{letter.deliver_at.strftime('%Y-%m-%d %H:%M UTC')}."
        )
    )
