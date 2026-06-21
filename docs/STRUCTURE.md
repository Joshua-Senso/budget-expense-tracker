# Expense Tracker — Repository Structure

Monorepo: frontend (Vercel) + services (auth, api) + infra + tests.

Agent instructions use `AGENTS.md` as the source of truth at each level, with a one-line `CLAUDE.md` importing it (`@AGENTS.md`). Root-level files load at startup; per-package files load on demand when the agent works in that package; sibling packages stay out of context.

This document maps the monorepo's **top level and shared conventions only**. Each project's *internal* structure and design pattern lives in its own `AGENTS.md` (e.g. `frontend/AGENTS.md`) and is intentionally not duplicated here — one source of truth per workspace. Project subtrees below are shown collapsed.

Local dev runs the apps on the host (`make api` / `auth` / `web`) against the dev compose backing services on plain `localhost` ports — no reverse proxy or local TLS. The base/prod compose and `cloudflared` ingress are for the deployed host only.

```text
expense-tracker/                        # monorepo root
│
├── README.md                           # overview + quick start
├── AGENTS.md                           # source of truth: repo map + global conventions
├── CLAUDE.md                           # one-liner: @AGENTS.md + Claude-only notes
├── CLAUDE.local.md                     # personal agent notes (git-ignored)
├── .gitignore                          # node_modules, .venv, .env, __pycache__
├── .editorconfig
├── Makefile                            # common dev commands (up, seed, migrate, lint, test)
│
├── docs/
│   ├── PRD.md                          # product requirements
│   ├── ARCHITECTURE.md                 # implementation / topology
│   ├── STRUCTURE.md                    # this file — monorepo map + per-workspace pointers
│   └── DEVELOPMENT.md                  # local dev: make targets, localhost ports, seeding
│
├── frontend/                           # Next.js web app (Vercel "root directory")
│   └── …                               # feature-first; pattern → frontend/AGENTS.md
│
├── services/
│   ├── auth/                           # Better Auth on Bun. Thin; pattern → services/auth/AGENTS.md
│   │
│   └── api/                            # FastAPI + arq worker (Python). Pattern → services/api/AGENTS.md
│
├── infra/
│   ├── docker-compose.dev.yml          # local backing services: postgres, redis, minio
│   ├── docker-compose.yml              # prod base: postgres, redis, auth, api, worker
│   ├── docker-compose.prod.yml         # host overrides: cloudflared tunnel, real R2
│   ├── .env.example                    # dev defaults + app connection URLs
│   └── cloudflared/
│       └── config.yml                  # tunnel ingress: auth./api. → services
│
├── e2e/                                # cross-stack end-to-end (Playwright)
│   ├── playwright.config.ts            # runs against the dev compose stack
│   ├── fixtures/                       # seeded users + households
│   └── tests/
│       ├── auth.spec.ts                # social sign-in, multi-provider linking
│       ├── expenses.spec.ts            # create/edit/delete, filters, month totals
│       ├── households.spec.ts          # invite → accept → shared view, roles
│       └── themes.spec.ts              # per-workspace theme switching
│
├── scripts/
│   ├── seed.py                         # dev seed data
│   └── backup.sh                       # pg_dump → R2 / MinIO
│
└── .github/
    └── workflows/
        ├── ci.yml                      # frontend vitest · auth vitest · api pytest · e2e
        ├── build.yml                   # build images → ghcr.io
        └── deploy.yml                  # pull + restart on the host
```
