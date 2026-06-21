# Development

Local dev runs the three apps on the host (hot reload) against backing services
in Docker. Everything is plain `localhost:<port>` — no reverse proxy or TLS.

| Service | URL | Run with |
|---------|-----|----------|
| API (FastAPI) | http://localhost:8000 | `make api` |
| Frontend (Next.js) | http://localhost:3000 | `make web` |
| Auth (Better Auth) | http://localhost:4000 | `make auth` |
| Postgres | localhost:5432 | `make up` |
| Redis | localhost:6379 | `make up` |
| MinIO (R2 in dev) | http://localhost:9000 (console :9001) | `make up` |

## Prerequisites

- Docker (Desktop)
- [uv](https://docs.astral.sh/uv/) — Python
- [Bun](https://bun.sh) — auth service
- [pnpm](https://pnpm.io) + Node — frontend / e2e

## Task tracking (Linear) — required

Work is driven by **Linear issues** (root `AGENTS.md` → Task tracking). Connect
Linear's MCP server in whatever coding agent you use, then authenticate (OAuth).
The setup is tool-specific but the server is the same:

```
Linear remote MCP endpoint:  https://mcp.linear.app/mcp   (streamable HTTP)
```

- **Claude Code** — pre-configured in this repo's `.mcp.json`; run `/mcp` and
  authenticate `linear`.
- **Codex / stdio-only clients** — register an MCP server that runs
  `npx -y mcp-remote https://mcp.linear.app/mcp` (bridges the remote server to
  stdio), then authenticate in the browser.
- **OpenCode / other MCP clients** — add the remote URL above per the client's MCP
  config, then authenticate.
- See Linear's MCP docs for the latest per-client steps.

Whatever the tool, the rule is the same: **no Linear connection → the agent stops
and asks you to set it up.** The issue is the spec; there's no task context without it.

## Quick start

```bash
make install                 # frontend (pnpm) + auth (bun) + api (uv sync)
cp infra/.env.example infra/.env   # optional — the dev stack boots on defaults
make up                      # postgres, redis, minio
make api                     # + make auth + make web, each in its own terminal
```

```bash
make down    # stop backing services (data kept in named volumes)
make reset   # stop AND wipe all local data
```

## Building features

The apps start minimal (a `/health` endpoint, a placeholder auth/web). As you
implement features, add files following **`docs/STRUCTURE.md`** — it defines
where things live (models, routers, services, components, lib) so the codebase
stays consistent. Per-service setup is introduced when its feature lands, e.g.:

- **API data layer** — add SQLAlchemy models under `app/models`, Alembic for
  app-table migrations, and the deps the code imports (`uv add ...`).
- **Auth** — `bun add better-auth`, configure providers + `jwt()`/`organization()`,
  then `bunx @better-auth/cli generate && migrate`.
- **Object storage** — receipts via presigned MinIO/R2 URLs (PRD §9.6).

## Tests

E2E uses Playwright (`cd e2e && pnpm exec playwright test`, expects the stack
running). Unit/component tests are added per package as features are built.
