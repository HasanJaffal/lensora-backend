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
`NotFoundError`, `ValidationError`, `ConflictError`, `UnauthorizedError`) and
converted to the error envelope by the handlers in [`common/handlers.py`](src/app/common/handlers.py)
with the correct HTTP status. Request validation failures return per-field `error.details[]`.

Every `error.code` is a stable, dot-namespaced key from the registry in
[`common/error_codes.py`](src/app/common/error_codes.py) (e.g. `patient.notFound`,
`inventory.outOfStock`, `attachment.notFound`). **These codes are the contract with the frontend
translation layer** (`backend-error-keys.ts`) — treat additions or renames as API changes.

## Requirements

- [Docker](https://docs.docker.com/get-docker/) with Compose — **the only supported way to run the
  backend locally**.
- [uv](https://docs.astral.sh/uv/) — needed only for the quality gate (lint/typecheck/test) and for
  authoring migrations, not for running the app.

## Running

`docker compose` is the single local-development run path for the backend. There is no bare-host
`uvicorn` workflow.

```bash
cp .env.example .env   # first time only
docker compose up --build
```

Compose starts `db` first, waits for its `pg_isready` healthcheck, then builds and starts `api`. On
every start the `api` container runs `alembic upgrade head` against `DATABASE_URL` before `uvicorn`
serves — migrations are applied automatically, there is no separate manual step. The API is
published on `API_PORT` (default `8000`):

```bash
curl http://127.0.0.1:8000/health
# {"success": true, "data": {"status": "ok"}, "error": null, "meta": null}
```

Both services read configuration exclusively from this repo's `.env`; nothing is baked into the
image. To publish on a different host port, set `API_PORT` before running compose.

The frontend is **not** part of this compose stack — it runs locally with `npm run dev` against the
composed API. See [`../lensora-frontend/README.md`](../lensora-frontend/README.md).

## Configuration

All configuration is read from the environment via `pydantic-settings` (`app/core/config.py`); an
optional `.env` file is loaded if present. Nothing is hardcoded. Every variable is documented with
safe placeholder values in [`.env.example`](.env.example). Create your local `.env` from it:

```bash
cp .env.example .env
```

Settings keys: `APP_ENV`, `API_PORT`, `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_DB`, `SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRES_MINUTES`, `CORS_ORIGINS`.

There is no environment-level seed account and no global deposit setting: every organization and
its admin account come from an explicit `provision_organization` run (below), and the deposit
percentage is a per-organization value passed at provisioning time.

## Developer tasks

There is no `Makefile` — run the `uv` commands directly. Running the application is not among them:
that is `docker compose up` only (see "Running" above).

| Task          | Command                                            |
|---------------|----------------------------------------------------|
| Install       | `uv sync`                                          |
| Lint          | `uv run ruff check`                                |
| Type-check    | `uv run mypy src`                                  |
| Test          | `uv run pytest`                                    |
| Quality gate  | `uv run ruff check && uv run mypy src && uv run pytest` |
| New migration | `uv run alembic revision --autogenerate -m "..."`  |
| Migrate       | `uv run alembic upgrade head`                      |
| Downgrade     | `uv run alembic downgrade -1`                      |

`uv sync` creates the virtual environment and installs runtime + dev dependencies with the `app`
package in editable mode. It is required only for the tasks above; the running app uses the image
built by compose.

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
uv run alembic revision --autogenerate -m "add patients"   # review migrations/versions/<rev>.py
uv run alembic upgrade head      # apply to head
```

`uv run alembic upgrade head` from the host is only needed to apply a migration you just authored
against the compose database without rebuilding. Running the stack via `docker compose up` applies
migrations automatically on container start (see "Running" above) — no manual step required there.

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
not a global setting. Run this against a migrated database; it requires `DATABASE_URL` to be
reachable the same way `uv run alembic upgrade head` does. With the stack already running, the
equivalent inside the container is
`docker compose exec api python -m app.management.provision_organization ...`.

## Provisioning the platform admin

The single `PLATFORM_ADMIN` account is provisioned the same way, by a developer with database
access — never from an environment variable and never seeded at app startup. It signs in through
the same `/login` form as any tenant admin and lands in the platform-admin section, which has its
own sidebar: a **Dashboard** tab (platform-wide organization counts) and an **Organization
Management** tab (list organizations, provision new ones, activate/deactivate them).

```bash
uv run python -m app.management.provision_platform_admin \
    --email admin@lensora.example --password change-me \
    --display-name-en "Platform Admin" --display-name-ar "مسؤول المنصة"
```

Re-running with an existing email fails cleanly unless `--rotate-password` is passed, in which case
it updates the password and display names on the existing account instead of creating a new one.
