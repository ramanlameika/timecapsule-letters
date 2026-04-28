# TimeCapsule Letters 💌

> Write a letter today. Receive it in the future.

An anonymous, open-source "future letter" app — write a message now, choose a delivery date, and it will be sent to your inbox when the time comes.

---

## ✨ Features

- **Anonymous (email-only)** — no accounts required
- **Email verification** before a letter is scheduled
- **Encrypted at rest** — letter bodies are encrypted with [Fernet](https://cryptography.io/en/latest/fernet/)
- **Background delivery** via Celery + Redis
- **Development mode** — emails are printed to logs when SMTP is not configured

---

## 🏗️ Architecture

```
┌─────────┐     POST /letters      ┌──────────────────────┐
│ Client  │ ───────────────────▶   │  FastAPI (api)        │
│         │ ◀───────────────────   │  app/main.py          │
└─────────┘  letter_id + message   └──────────┬───────────┘
                                              │ writes
                                              ▼
                                    ┌─────────────────┐
                                    │   PostgreSQL     │
                                    │   (letters)      │
                                    └─────────────────┘
                                              ▲
                                              │ reads/writes
                                   ┌──────────┴──────────┐
                                   │  Celery Worker       │
                                   │  (worker + beat)     │
                                   │  app/tasks.py        │
                                   └──────────────────────┘
```

### Services

| Service    | Description                                          |
|------------|------------------------------------------------------|
| `api`      | FastAPI HTTP server (uvicorn)                        |
| `worker`   | Celery worker — sends due letters                    |
| `beat`     | Celery beat — triggers delivery sweep every minute   |
| `postgres` | PostgreSQL 16 — persists letters                     |
| `redis`    | Redis 7 — Celery broker & result backend             |

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/) v2+

### 1. Clone the repository

```bash
git clone https://github.com/ramanlameika/timecapsule-letters.git
cd timecapsule-letters
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Generate an encryption key and paste it into `.env`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set `LETTER_ENCRYPTION_KEY=<generated key>` in `.env`.

> **Development mode**: Leave `SMTP_HOST` empty and set `ENVIRONMENT=dev`.
> Emails will be printed to the `api` / `worker` logs instead of being sent.

### 3. Start the stack

```bash
docker compose up --build
```

The API is available at **http://localhost:8000**.

Interactive docs: **http://localhost:8000/docs**

---

## 📡 API Endpoints

### `GET /healthz`

```json
{"status": "ok"}
```

### `POST /letters`

Create a future letter.

**Request body:**

```json
{
  "email_to": "me@example.com",
  "subject": "Hello from the past!",
  "body": "Dear future me...",
  "deliver_at": "2026-01-01T09:00:00Z"
}
```

**Response `201`:**

```json
{
  "letter_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "message": "Letter created. Check your inbox for a verification link. ..."
}
```

### `GET /letters/verify?token=...&letter_id=...`

Verify ownership of the email address. The link is included in the
verification email sent after `POST /letters`.

**Response `200`:**

```json
{
  "message": "Email verified! Your letter is now scheduled for delivery on 2026-01-01 09:00 UTC."
}
```

---

## 🔐 Security Notes

- Letter bodies are encrypted with **Fernet symmetric encryption** before being written to the database.
- Verification tokens are **never stored in plaintext** — only a SHA-256 hash is persisted.
- After a token is used it is cleared from the database (single-use).
- The `LETTER_ENCRYPTION_KEY` should be treated as a secret; rotate it via a key-migration script (not included in this MVP).

---

## 🛠️ Development

### Run without Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set env vars (or export them manually)
export DATABASE_URL=postgresql://timecapsule:timecapsule@localhost:5432/timecapsule
export REDIS_URL=redis://localhost:6379/0
export LETTER_ENCRYPTION_KEY=<your key>
export ENVIRONMENT=dev

# Apply migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload

# Start worker (in another terminal)
celery -A app.tasks.celery_app worker --loglevel=info

# Start beat scheduler (in another terminal)
celery -A app.tasks.celery_app beat --loglevel=info
```

### Database migrations

```bash
# Create a new migration after changing models
cd backend
alembic revision --autogenerate -m "describe change"

# Apply pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

---

## 📁 Project Structure

```
timecapsule-letters/
├── backend/
│   ├── app/
│   │   ├── config.py       # Pydantic Settings (env vars)
│   │   ├── crypto.py       # Fernet encryption helpers
│   │   ├── db.py           # SQLAlchemy engine & session
│   │   ├── email.py        # SMTP / dev-log email sender
│   │   ├── main.py         # FastAPI app & routes
│   │   ├── models.py       # SQLAlchemy 2.0 ORM models
│   │   ├── schemas.py      # Pydantic request/response schemas
│   │   └── tasks.py        # Celery tasks (delivery sweep)
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── 0001_initial_schema.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🗺️ Roadmap / Contributing

Ideas for future contributions (good first issues):

- [ ] Cancel a letter before delivery
- [ ] Resend verification email
- [ ] Writing prompts / mood tags
- [ ] Time capsule image attachment
- [ ] Rate limiting (slowapi)
- [ ] Frontend UI (Next.js / plain HTML)
- [ ] One-click Render / Fly.io deploy

Open an issue or PR — all contributions welcome! 🎉

---

## 📄 License

[MIT](LICENSE)
