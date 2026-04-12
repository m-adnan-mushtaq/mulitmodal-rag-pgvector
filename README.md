# SitenSight API

FastAPI app with async SQLAlchemy 2, Alembic, PostgreSQL and pgvector. Feature-based project structure.

## Stack

- **FastAPI** – API framework
- **SQLAlchemy 2** – async ORM
- **Alembic** – migrations
- **PostgreSQL** – database (with pgvector extension)
- **uvicorn** – ASGI server
- **pydantic-settings** – type-safe env config (see `app/core/config.py`)

## Project structure

```
app/
  api/          # Route handlers
  core/         # Config and app-wide setup
  db/           # Database engine, session, Base
  services/     # Feature services
  alembic/      # Migrations
```

## Setup

### 1. Virtual environment

```bash
python -m venv .venv
# or
python3 -m venv .venv
```

Activate it:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

To lock versions (e.g. for production), install then export:

```bash
pip freeze > requirements-lock.txt
```

### 3. Environment variables

Copy the example env and set values:

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL settings.

### 4. Run with Docker (API + DB)

Start database and API:

```bash
docker compose up --build
```
- API: http://localhost:8000  
- Health: http://localhost:8000/health  
- Docs: http://localhost:8000/docs  

The API container uses `POSTGRESQL_SERVER=db`, so it talks to the Postgres container. pgvector is enabled via the first migration.

### 5. Run migrations (with Docker)

With Docker containers running, you can run Alembic migrations inside the API container:

**Upgrade to latest migration:**
```bash
docker compose exec api alembic upgrade head
```

**Create a new migration with autogeneration:**
```bash
docker compose exec api alembic revision --autogenerate -m "add vector table"
```

If you are not using Docker, you can run the following with your local environment:

```bash
alembic upgrade head
```

```

### 6. Run locally (no Docker)

With Postgres (and pgvector) running locally and `.env` set:

```bash
uvicorn app.main:app --reload
```

Or with the FastAPI CLI:

```bash
fastapi dev app/main.py
```
Run the celery worker

```bash
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

Run the seeders
```bash 
python -m app.seeders.roles_seeder
python -m app.seeders.admin_seeder
```

## Endpoints

- **GET /health** – Returns `{"status": "ok"}` (200).

## Adding env variables

Add fields to `app/core/config.py`; pydantic-settings reads from `.env` and the environment.

## Adding features

Use the feature-based layout: new routes under `app/api/`, services under `app/services/`, and models under `app/db/` or a feature module as you grow.
