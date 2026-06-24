# Expense Tracker

A private web app for tracking personal and shared-household expenses, monthly
budget health, and spending patterns — multi-currency, with social sign-in.

- **Product spec:** [`docs/PRD.md`](docs/PRD.md)
- **Architecture:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Local dev guide:** [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js + Tailwind/shadcn (Vercel) |
| API | FastAPI + arq worker (Python 3.12, uv) |
| Auth | Better Auth on Bun (OAuth, households, JWKS) |
| Data | PostgreSQL, Redis, Cloudflare R2 (MinIO in dev) |
| Edge | Cloudflare (DNS, TLS, WAF, Tunnel) |

## Quick start

```bash
make install   # frontend (pnpm) + auth (bun) + api (uv)
make up        # start postgres, redis, minio in Docker
make api       # http://localhost:8000
make web       # http://localhost:3000
make auth      # http://localhost:4000
```

Run `make` with no arguments to list all commands. See `docs/DEVELOPMENT.md`
for one-time setup (deps, DB migrations, seeding).
