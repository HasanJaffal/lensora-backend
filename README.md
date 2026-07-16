# Lensora — Backend

FastAPI backend for Lensora, a multi-tenant optometrist practice management platform. Each
organization (tenant) is provisioned with exactly one `ORGANIZATION_ADMIN` account and gets fully
isolated patients, inventory, catalogs, and orders.

Layered, SOLID architecture: `routers → schemas (DTOs) → services → repositories → models`.
Tenant isolation is enforced at the repository layer via `TenantScopedRepository`
(`get_scoped`/`scoped_select`/`add_scoped`) bound to a per-request `TenantContext`. See
[`CLAUDE.md`](CLAUDE.md) for the full engineering standards, including tenancy invariants, audit
rules, and roles. Requirements and the original implementation plan live in the parent workspace's
[`business_requirement.md`](../business_requirement.md) and [`tasks/`](../tasks/).

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
`POSTGRES_DB`, `SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRES_MINUTES`, `CORS_ORIGINS`,
`AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL`.

There is no environment-level seed account and no global deposit setting: every organization and
its admin account come from an explicit `provision_organization` run (below), and the deposit
percentage is a per-organization value passed at provisioning time.

## Running with Docker

The backend and a PostgreSQL database run together via [`docker-compose.yml`](docker-compose.yml)
in this repo:

```bash
cp .env.example .env   # first time only
docker compose up --build
```

Compose starts `db` first, waits for its `pg_isready` healthcheck, then builds and starts `api`.
The API is published on `API_PORT` (default `8000`):

```bash
curl http://127.0.0.1:8000/health
```

Both services read configuration exclusively from this repo's `.env`; nothing is baked into the
image. To publish on a different host port, set `API_PORT` before running compose.

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

## Provisioning organizations

Lensora is multi-tenant: there is no environment-seeded account. Every organization and its single
`ORGANIZATION_ADMIN` account are created by running the `provision_organization` management
command, which also seeds that organization's default lens catalog and tips:

```bash
uv run python -m app.management.provision_organization \
    --org-name "Acme Optometry" --org-slug acme \
    --admin-email admin@acme.com --admin-password change-me \
    --admin-display-name-en "Dr. Jane Doe" --admin-display-name-ar "د. جين دو" \
    --deposit-percent 0.40
```

`--org-slug` and `--admin-email` must each be globally unique; re-running with the same slug/email
fails cleanly rather than duplicating data. `--deposit-percent` is optional (defaults to `0.40`) and
sets that organization's lens-order deposit fraction — deposit percent is a per-organization value,
not a global setting. Run this against a migrated database (`make migrate` first); it requires
`DATABASE_URL` to be reachable the same way `make migrate` does.
