# Alembic Migrations

Alembic owns only FastAPI application tables. Better Auth owns its plural tables
through its CLI (`users`, `sessions`, `accounts`, `verifications`, `jwks`,
`organizations`, `members`, and `invitations`).

`migrations/env.py` uses `include_object` from `app.core.db` so autogenerate does
not create, alter, or drop Better Auth tables.

Workflow:

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

Always review generated revisions before applying them.
