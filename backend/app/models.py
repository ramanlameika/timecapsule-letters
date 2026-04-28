"""SQLAlchemy 2.0 models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db import Base


class Letter(Base):
    __tablename__ = "letters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email_to: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Body stored encrypted (Fernet token, base64 encoded)
    encrypted_body: Mapped[str] = mapped_column(Text, nullable=False)

    deliver_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Status lifecycle:
    # pending_verification → scheduled → sent
    #                                  ↘ failed
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending_verification"
    )

    # Verification: store only a SHA-256 hash of the token
    verify_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Delivery error message (if any)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
