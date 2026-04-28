"""Pydantic request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class LetterCreate(BaseModel):
    email_to: EmailStr
    subject: str | None = None
    body: str
    deliver_at: datetime

    @field_validator("deliver_at")
    @classmethod
    def deliver_at_must_be_future(cls, v: datetime) -> datetime:
        from datetime import timezone

        now = datetime.now(tz=timezone.utc)
        # Ensure the value is timezone-aware for comparison
        if v.tzinfo is None:
            from datetime import timezone as tz

            v = v.replace(tzinfo=tz.utc)
        if v <= now:
            raise ValueError("deliver_at must be a future datetime")
        return v


class LetterCreateResponse(BaseModel):
    letter_id: uuid.UUID
    message: str


class VerifyResponse(BaseModel):
    message: str
