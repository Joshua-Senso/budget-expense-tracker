# api — Agent Guide

Business APIs + an arq background worker, one codebase. **FastAPI**, **Python
3.12** (managed with **uv**), **SQLAlchemy 2.0 (sync)**, **pydantic v2**,
**Alembic**, **arq**. Identity comes from Better Auth; this service verifies the
JWT and owns all application data.

The repo-wide layout is in `docs/STRUCTURE.md`; the rules here win for anything
under `services/api/`.

## Architecture: feature-first, layered within a feature

Group by **domain feature** (matches the frontend). Within each feature, keep a
strict **router → service → model** layering. Cross-cutting concerns live in
`core/`.

```text
app/
  main.py            # app factory: builds FastAPI, includes each feature's router
  core/
    config.py        # pydantic-settings (required vars fail fast — no localhost defaults)
    db.py            # engine, Session, DeclarativeBase, get_db(), session_scope()
    redis.py         # shared Redis client
    security.py      # get_current_user_id — verify Bearer JWT via JWKS (PyJWKClient)
  features/<domain>/  # expenses, categories, recurring, budget, dashboard,
    router.py        #   currency, import-export, attachments …
    service.py
    models.py
    schemas.py
  worker/
    settings.py      # arq WorkerSettings
    tasks.py         # recurring gen · FX refresh · backups · heavy imports
migrations/          # Alembic — APP TABLES ONLY
tests/               # pytest (added per feature as built)
```

## Layer responsibilities (do not blur these)

- **`router.py`** — thin HTTP only. An `APIRouter`, endpoints depend on
  `get_current_user_id` and `get_db`, then delegate to the service. No business
  logic, no multi-step ORM queries here.
- **`service.py`** — all business logic. Takes a `Session` + `user_id` (+ inputs),
  returns domain data. **Never imports FastAPI/HTTP** — that keeps it unit-testable
  and reusable by the worker.
- **`models.py`** — SQLAlchemy 2.0 typed models (`Mapped[...]`), inheriting the
  `Base` from `core/db.py`.
- **`schemas.py`** — pydantic v2 request/response models. Kept separate from ORM
  models; never return ORM objects directly.

## Rules

- **Sync DB.** `def` endpoints with a sync `Session` from `get_db`. Use
  `session_scope()` in worker tasks/scripts. The worker is async (arq) but calls
  into the same sync services.
- **Authorization, every query.** Scope to the authenticated `user_id`; for shared
  rows, also check household membership and role (PRD §10). Expense/recurring
  writes may only reference categories owned by the user or their household.
- **Alembic owns ONLY app tables.** `migrations/env.py` filters with
  `include_object` so autogenerate never touches Better Auth's (plural) tables
  (`users`, `sessions`, `organizations`, …). Workflow: edit `models.py` →
  `uv run alembic revision --autogenerate -m "…"` → **review the diff** →
  `uv run alembic upgrade head`. Make sure every feature's models are imported
  into `Base.metadata` before autogenerate (import them in `migrations/env.py`).
- **Money.** Store original `amount` + `currency` and converted `base_amount` +
  `exchange_rate`. Conversion is a service using FX rates cached in Redis; default
  base currency PHP (PRD §7.10).
- **Receipts.** Presigned R2/MinIO URLs via boto3; file bytes never pass through
  the API (PRD §9.6). The DB stores only the object key.
- **Excel.** Service parses + validates; no partial writes on validation failure;
  idempotency keys in Redis; large imports offloaded to the worker (PRD §7.8).
- **Config.** `core/config.py` makes environment-specific/secret values **required**
  (no defaults) so a misconfigured prod fails fast. Dev values live in `.env`.
- **Naming.** snake_case modules/functions, PascalCase models & schemas.

## Recipe — adding a domain feature

1. `app/features/<name>/models.py` — SQLAlchemy models (inherit `core` `Base`).
2. `schemas.py` — pydantic request/response models.
3. `service.py` — business logic over a `Session`, scoped to `user_id`/household.
4. `router.py` — `APIRouter`, thin endpoints depending on auth + `get_db`.
5. Register: import the router in `main.py`; ensure models are imported for Alembic.
6. `uv run alembic revision --autogenerate -m "<name>"` → review → `upgrade head`.

## Dependencies

Managed with **uv** (`uv add <pkg>` / `uv add --dev <pkg>`; lockfile `uv.lock`).
The service starts minimal (`/health`); add deps when you implement the layer
that needs them — typically `sqlalchemy`, `psycopg[binary]`, `pyjwt`, `redis`,
`arq`, `boto3`, `openpyxl`.

## Commands

```
make api                              # from repo root — dev server (:8000)
uv run uvicorn app.main:app --reload  # same, from services/api
uv run arq app.worker.settings.WorkerSettings   # background worker
uv run pytest                         # tests
uv run ruff check . && uv run ruff format .
uv run alembic revision --autogenerate -m "…"   # then: uv run alembic upgrade head
```

Rule of thumb: **Makefile = run the service; uv = Python/api-specific tasks.**
