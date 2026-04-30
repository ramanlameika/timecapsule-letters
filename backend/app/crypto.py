"""Fernet-based encryption helpers for letter bodies."""

import logging

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    key = settings.letter_encryption_key
    if not key:
        raise RuntimeError(
            "LETTER_ENCRYPTION_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


def encrypt_body(plaintext: str) -> str:
    """Encrypt a letter body and return a base64-encoded token string."""
    f = _get_fernet()
    token: bytes = f.encrypt(plaintext.encode())
    return token.decode()


def decrypt_body(token: str) -> str:
    """Decrypt a Fernet token back to the plaintext body."""
    f = _get_fernet()
    try:
        plaintext: bytes = f.decrypt(token.encode())
        return plaintext.decode()
    except InvalidToken as exc:
        logger.error("Failed to decrypt letter body: %s", exc)
        raise
