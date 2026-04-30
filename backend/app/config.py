"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://timecapsule:timecapsule@postgres:5432/timecapsule"

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"

    # Encryption – generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    letter_encryption_key: str = ""

    # SMTP (leave empty to use dev log-only mode)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@timecapsule.local"
    smtp_tls: bool = True

    # Public base URL used in verification links
    base_url: str = "http://localhost:8000"

    # Set to "dev" to skip real SMTP and log emails instead
    environment: str = "dev"


settings = Settings()
