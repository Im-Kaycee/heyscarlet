# HeyScarlet — Backend

FastAPI backend for the HeyScarlet MVP.

## Stack
- **Framework:** FastAPI + Python
- **Database:** PostgreSQL (Railway) via SQLModel + Alembic
- **AI:** Google Gemini API (streaming)
- **Auth:** JWT via python-jose

## Setup

```bash
# 1. Clone and install dependencies
pip install -r requirements.txt

# 2. Copy and fill environment variables
cp .env.example .env

# 3. Run migrations
alembic upgrade head

# 4. Start development server
uvicorn app.main:app --reload
```

## Running Migrations

```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

## Project Structure

```
app/
├── api/routes/       # Route handlers (auth, chat)
├── core/             # Config, security utilities
├── db/               # Database session
├── models/           # SQLModel table definitions (source of truth)
├── schemas/          # Pydantic request/response schemas
├── services/         # Gemini streaming service
└── main.py           # App entry point
alembic/              # Migration scripts
```

## Developer Notes

- **Auth dependency** (Ijudigal): implement `get_current_user` in `app/core/dependencies.py`
  and wire it into `/auth/me` and `/chat/stream`
- **Conversation endpoints** (Nandom): implement `list_conversations` and `get_messages`
  in `app/api/routes/chat.py`
- All models live in `app/models/` — do not modify schemas without team discussion
- Commit every 3 business days minimum (contract requirement)