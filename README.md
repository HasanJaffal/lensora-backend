# Sour Optic — Backend

FastAPI backend for the Sour Optic optometrist practice management platform.

Layered, SOLID architecture: `routers → schemas (DTOs) → services → repositories → models`.
The app factory, configuration, `/health` endpoint (Task 01), Docker/environment (Task 02), the
async database + code-first migration layer (Task 03), and the shared response envelope + error
handling (Task 04) are in place. Domain models (Task 06) are added by later tasks.

## Response envelope & errors

Every endpoint returns the shared envelope from [`src/app/common/envelope.py`](src/app/common/envelope.py)
— `{ success, data, error, meta }`, serialized as **camelCase** JSON. Use the `ok(data, meta=None)`
and `fail(code, message, details=None)` helpers rather than hand-building responses. List endpoints
attach `PaginationMeta` under `meta.pagination` and take the `PageParams` dependency
(`?page=&pageSize=`).

Errors are raised as domain exceptions ([`common/exceptions.py`](src/app/common/exceptions.py):
`NotFoundError`, `ValidationError`, `ConflictError`, `UnauthorizedError`, `AIUnavailableError`) and
converted to the error envelope by the handlers in [`common/handlers.py`](src/app/common/handlers.py)
with the correct HTTP status. Request validation failures return per-field `error.details[]`.

Every `error.code` is a stable, dot-namespaced key from the registry in
[`common/error_codes.py`](src/app/common/error_codes.py) (e.g. `patient.notFound`,
`inventory.outOfStock`, `ai.unavailable`). **These codes are the contract with the frontend
translation layer** (`backend-error-keys.ts`) — treat additions or renames as API changes.

## Requirements

- [uv](https://docs.astral.sh/uv/) (manages the Python 3.12 toolchain and dependencies)

## Setup

```bash
uv sync
```

This creates a virtual environment, installs runtime + dev dependencies, and installs the `app`
package in editable mode.

## Running

```bash
uv run uvicorn app.main:app --reload
```

Then check the health endpoint:

```bash
curl http://127.0.0.1:8000/health
# {"success": true, "data": {"status": "ok"}, "error": null, "meta": null}
```

## Configuration

All configuration is read from the environment via `pydantic-settings` (`app/core/config.py`); an
optional `.env` file is loaded if present. Nothing is hardcoded. Every variable is documented with
safe placeholder values in [`.env.example`](.env.example). Create your local `.env` from it:

```bash
cp .env.example .env
```

Settings keys: `APP_ENV`, `API_PORT`, `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_DB`, `SECRET_KEY`, `CORS_ORIGINS`, `DEPOSIT_PERCENT`, `AI_PROVIDER`, `AI_API_KEY`,
`AI_MODEL`.

## Running with Docker

The backend and a PostgreSQL database run together via docker compose, defined in the parent
workspace wrapper (`../docker-compose.yml`), which references this repo as `sour-optic-backend/`.
From that wrapper directory:

```bash
cp sour-optic-backend/.env.example sour-optic-backend/.env   # first time only
docker compose up --build
```

Compose starts `db` first, waits for its `pg_isready` healthcheck, then builds and starts `api`.
The API is published on `API_PORT` (default `8000`):

```bash
curl http://127.0.0.1:8000/health
```

Both services read configuration exclusively from `sour-optic-backend/.env`; nothing is baked into
the image. To publish on a different host port, run compose with that value exported for
interpolation, e.g. `docker compose --env-file sour-optic-backend/.env up` after setting `API_PORT`.

## Developer tasks

A `Makefile` wraps the common commands. On systems without `make`, run the underlying `uv`
commands directly:

| Task       | Make target      | Raw command                              |
|------------|------------------|------------------------------------------|
| Install    | `make install`   | `uv sync`                                |
| Lint       | `make lint`      | `uv run ruff check`                      |
| Type-check | `make typecheck` | `uv run mypy src`                        |
| Test       | `make test`      | `uv run pytest`                          |
| Run        | `make run`       | `uv run uvicorn app.main:app --reload`   |
| Migrate    | `make migrate`   | `uv run alembic upgrade head`            |
| New migration | `make makemigration name="..."` | `uv run alembic revision --autogenerate -m "..."` |
| Downgrade  | `make downgrade` | `uv run alembic downgrade -1`            |

## Database & migrations

The async SQLAlchemy layer lives in [`src/app/db/`](src/app/db): `engine.py` (async engine +
session factory), `session.py` (the `get_session` FastAPI dependency), `unit_of_work.py`
(transaction boundary for multi-table writes), `base.py` (declarative `Base` with a deterministic
constraint naming convention plus reusable id/timestamp mixins), and `registry.py` (imports every
feature model so autogenerate sees the full schema).

Migrations are **code-first**: change the models, then autogenerate and **review the result by
hand** — Alembic emits renames as drop+add, which would drop data if applied blindly. One migration
per logical schema change; never edit a migration that has already been applied. Seed data lives in
`db/seed.py`, never in migrations.

```bash
docker compose up -d db          # a running Postgres is required
make makemigration name="add patients"   # then review migrations/versions/<rev>.py
make migrate                     # apply to head
```

The migration URL is injected from `DATABASE_URL` in `migrations/env.py`; it is never hardcoded in
`alembic.ini`. When running Alembic against the compose database from the host, point `DATABASE_URL`
at `localhost` (the `db` hostname only resolves inside the compose network).
