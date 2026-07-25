# Engineering Standards — Lensora Backend

Authoritative rules for anyone (human or agent) writing code in this repository. The goal is **clean, SOLID, senior production-level code with no flaws**. When a task description and these standards conflict, these standards win.

Requirements: [`../business_requirement.md`](../business_requirement.md). Plan: [`../tasks/`](../tasks/).

---

## Core principles

1. **SOLID, always.**
   - *Single responsibility* — a function, class, or component does one thing. Split data access, business logic, and presentation.
   - *Open/closed* — extend via new implementations, not by editing stable code.
   - *Liskov* — substitutable implementations honor the same contract (the fallback AI provider must be a drop-in for the Gemini one).
   - *Interface segregation* — keep interfaces/protocols narrow and purpose-built.
   - *Dependency inversion* — depend on abstractions (protocols, interfaces), inject them; never construct concrete dependencies inside business logic.

2. **No flaws.** Handle every error path, validate all input at the boundary, never swallow exceptions, no unhandled promise rejections, no race conditions, no `any`/`# type: ignore` escape hatches. Guard against empty/null/out-of-range before use.

3. **Descriptive names.** Names state intent without a comment. `calculateLensOrderTotal`, `inStockFrames`, `PatientRefractionDto`, `useLowStockCount` — never `data`, `tmp`, `handle`, `doIt`, `mgr`, `x`. Booleans read as predicates (`isInStock`, `hasExpiredToken`). Functions are verbs; classes/types are nouns. See the **domain-abbreviation naming exception** below for optometry fields.

4. **No comments unless necessary.** Code explains itself through names and structure. Comment **only** to explain *why* for a non-obvious decision (a workaround, a domain rule, a deliberate tradeoff) — never *what* the code does. When a comment is warranted, keep it to one concise line. No commented-out code, no docstring noise restating the signature, no section-divider banners.

5. **Small units.** Prefer short functions and focused components. If a unit mixes fetching, formatting, business rules, and rendering, split it. Prefer composition over inheritance.

6. **Consistency over cleverness.** Match surrounding patterns. Don't introduce a second way to do something that already has a convention.

---

## Backend rules

- **Layering:** `routers → schemas (Pydantic DTOs) → services → repositories → models`. Each layer only talks to the one below it.
  - Routers: HTTP only (parse, delegate, return the envelope). No business logic, no ORM.
  - Services: business logic, orchestration, transactions (Unit of Work). Depend on repository abstractions.
  - Repositories: data access only. No business rules.
  - Models: SQLAlchemy tables only.
- **DTO separation is absolute.** Never return or accept a SQLAlchemy model across the API boundary. Requests are `*Request`, responses are `*Dto`. JSON is camelCase via Pydantic alias generator.
- **Response envelope:** every endpoint returns the shared envelope (`success/data/error/meta`). Use the `ok()` / `fail()` helpers. Errors carry a dot-namespaced `code` from the central registry and the correct HTTP status via the domain exception hierarchy. Keep codes in sync with the frontend `backend-error-keys`.
- **Migrations are code-first.** Change models, autogenerate with Alembic, then **review the migration by hand** (renames autogenerate as drop+add). One migration per logical change; never edit an applied migration. Seed data lives in `db/seed.py` / `db/seeds/`, never in migrations.
- **Config from settings only.** All configuration via `pydantic-settings` reading the environment. No literals for URLs, secrets, ports, keys.
- **AI features never block the workflow.** Gemini is the only supported AI service; every AI call has a deterministic fallback (NFR-4). Depend on the `AIProvider` abstraction, never a concrete client, in feature code.
- **Async throughout.** Async engine, async sessions, `async def` endpoints and services. No blocking I/O in the event loop.
- **Typing:** full type hints; `mypy` clean. No `Any` unless unavoidable and justified.
- **Bilingual by construction:** persist `*_en` / `*_ar` fields; do not concatenate or hardcode language in models.

## Tenancy invariants

Lensora is multi-tenant: every request executes inside the boundary of exactly one `organization`.

- **Never query a tenant-owned model unscoped.** Any model built on `TenantEntity` (see below) must be read, written, and deleted through the tenant-scoped repository base — never a raw `session.get(...)` or an unfiltered `select(...)`.
- **Always go through `TenantScopedRepository`** ([`db/repository.py`](src/app/db/repository.py)): `scoped_select(Model)` for filtered queries, `get_scoped(Model, id)` in place of `session.get`, `add_scoped(entity)` to stamp `organization_id` on insert. A feature repository for a tenant-owned model extends this base; it must never construct an unscoped statement.
- **The tenant boundary comes from `TenantContext`** ([`common/tenant_context.py`](src/app/common/tenant_context.py)), bound to a `ContextVar` — by the `get_tenant_context` FastAPI dependency for requests, or explicitly via the `tenant_context(ctx)` context manager for non-request paths (management commands, seeding).
- **`UserRepository` is the only intentionally-global repository.** Login resolves an account by email before any tenant is known, so `UserRepository` does not extend `TenantScopedRepository` and is the sole place a feature is allowed to query the `user_account` table unscoped. No other repository gets this exemption.
- **Composite uniqueness is per-tenant.** Natural keys that used to be globally unique (`inventory.sku`, `tip.title_en`, lens option names, etc.) are `(organization_id, …)` composite uniques — two organizations may reuse the same value. `user_account.email` remains globally unique; it is the login identity, not tenant-owned data.

## Audit & base entities

- **Two convenience bases** in [`db/base.py`](src/app/db/base.py): `Entity` (Uuid + Timestamp + Audit) for global models (`organization`, `user_account`), and `TenantEntity` (Uuid + Timestamp + Audit + Tenant) for tenant-owned models. Every new model inherits one of these — never compose the mixins by hand.
- **`created_by`/`updated_by` are never set by application code.** The mapper-level `before_insert`/`before_update` listeners in [`db/audit.py`](src/app/db/audit.py) are the single source of truth: they read the bound `TenantContext` and stamp the actor (and `organization_id`, for tenant-owned models) automatically. No service or repository sets these columns itself.
- Both columns are nullable: CLI/seed/system inserts run with no bound context, so the actor is left `null` by design — this is expected, not an error path to guard against.

## Roles

- `UserRole` has two values: **`ORGANIZATION_ADMIN`** and **`PLATFORM_ADMIN`**. There is no permission table beyond this; "authenticated" is equivalent to "authorized" within whichever scope the role grants.
- **`ORGANIZATION_ADMIN`** is the single account per organization, with full access to its own tenant. Its `organization_id` is always set and unique per organization (`uq_user_account_organization_id`, NULL-excluding — see below).
- **`PLATFORM_ADMIN`** is a single account with `organization_id = NULL`. It authenticates through the same `/auth/login` as any other account, but `UserDto`/`LoginResponse` carry `organization: null`, and `GET /auth/me` reflects the same. It is provisioned by a developer with server/DB access, the same posture as `provision_organization` — `python -m app.management.provision_platform_admin --email ... --password ... --display-name-en ... --display-name-ar ...` ([`management/provision_platform_admin.py`](src/app/management/provision_platform_admin.py)). There is **no env-var seeding and no startup hook**: the account only ever comes from an explicit, auditable provisioning run, and there is no self-registration or in-app creation of additional platform admins.
- **`get_tenant_context` rejects `PLATFORM_ADMIN` outright** (it requires a non-null `organization_id` by design). Platform-admin routes instead depend on `require_platform_admin` ([`common/deps.py`](src/app/common/deps.py)), which checks `current_user.role` directly and never binds a `TenantContext`.
- **Platform-admin routes are functionally separate from every tenant-scoped router.** They live in [`features/platform_admin/`](src/app/features/platform_admin/), are never reachable through `TenantScopedRepository`, and only ever return organization/account metadata (name, slug, admin email/display name, deposit percent, active status, timestamps) — never patient/inventory/clinical data. Provisioning a new organization is available both via this in-app API (`POST /api/v1/platform-admin/organizations`) and the original CLI script (`python -m app.management.provision_organization`, see [`README.md`](README.md)), which remains available for ops/scripting use; both paths call the same `OrganizationProvisioningService`.
- **The platform admin drives a second application section**, structurally parallel to the tenant app rather than a single utility screen: its own sidebar with a **Dashboard** tab (platform-wide organization counts, `GET /platform-admin/dashboard`) and an **Organization Management** tab (list, provision, activate/deactivate). This is still not a general user-management surface — it manages organizations and their one admin login each, with no multi-user-per-organization UI, no self-registration, and no invitation flow.
- **Organization suspension:** `Organization.is_active` is toggled via `PATCH /platform-admin/organizations/{id}/status`. Deactivating a tenant blocks its admin in `AuthService` at **both** `authenticate` and `resolve_token` — so existing sessions are revoked, not just new logins — raising `organization.deactivated`. This is distinct from `User.is_active`, which disables one account rather than a whole tenant; platform admins have no organization and are never gated by either check.
- Role assignment happens once, at provisioning time — by a developer/operator running the relevant management command for both organization admins and the platform admin.

## Domain-abbreviation naming exception

Optometry has its own standard vocabulary. The following are **declarative in the domain, not cryptic abbreviations**, and are kept intentionally rather than expanded to satisfy the general descriptive-naming rule:

- `od_*` / `os_*` — *oculus dexter* / *oculus sinister* (right/left eye), the standard clinical prefixes for per-eye refraction fields.
- `pd_*` — pupillary distance.
- `sph`, `cyl`, `axis`, `add` — sphere, cylinder, axis, near-vision addition: the standard refraction prescription fields.
- `sku` — stock keeping unit, standard inventory terminology.
- `spec` — a lens/frame specification value in the catalog.
- `rx_*` — prescription-related fields (`rx` is standard shorthand for "prescription" in optical and medical contexts).

Anywhere else in the codebase, write out the full word.

## Shared rules

- **Env hygiene:** real `.env` files are never committed and never baked into Dockerfiles/compose. Every variable is documented in the matching `.env.example`.
- **No dead code, no TODO litter, no unused deps.** Don't add a dependency without a clear justification that existing tools can't cover.
- **Errors are typed and surfaced**, never silently caught. Backend maps to error codes; frontend translates them.
- **Determinism in tests:** fixed seed, isolated DB, no reliance on wall-clock/network.

---

## Definition of done (per task)

- [ ] Behavior matches the referenced FR/NFR in [`../business_requirement.md`](../business_requirement.md).
- [ ] Layering, DTO separation, and naming rules above are honored.
- [ ] Tenancy invariants honored: no unscoped query/insert against a tenant-owned model.
- [ ] `ruff check` + `mypy` + `pytest` pass (`make lint typecheck test`).
- [ ] AI paths verified with the provider disabled.
- [ ] No hardcoded config, no stray comments, no `any`/`type: ignore`, no unhandled error paths.
