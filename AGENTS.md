# Expense Tracker — Agent Guide (root)

Monorepo for a private expense tracker. See `docs/PRD.md` (product),
`docs/ARCHITECTURE.md` (implementation), and **`docs/STRUCTURE.md` (repo layout +
file-placement pattern — follow it when adding files)**. This file is the source
of truth for repo-wide conventions; each package has its own `AGENTS.md` that
loads on demand.

The apps start minimal and grow feature by feature. Don't pre-create empty
modules — add a file when you implement what goes in it, placing it where
`docs/STRUCTURE.md` says.

## Layout

| Path | What it is | Stack |
|------|------------|-------|
| `frontend/`     | Web app (Vercel)            | Next.js, pnpm, TanStack Query |
| `services/api/` | Business APIs + arq worker  | FastAPI, Python 3.12, uv |
| `services/auth/`| Auth + households           | Better Auth on Bun |
| `infra/`        | Compose, cloudflared        | Docker |
| `e2e/`          | Cross-stack tests           | Playwright |
| `scripts/`      | Dev/ops helpers             | — |

## Local development

Backing services run in Docker; apps run on the host with hot reload.

```
make install   # deps for all three apps
make up        # postgres :5432, redis :6379, minio :9000/:9001
make api       # http://localhost:8000
make web       # http://localhost:3000
make auth      # http://localhost:4000
make down / make reset
```

No reverse proxy or local TLS — everything is plain `localhost:<port>`.

## Conventions

- Secrets live in per-package `.env` (gitignored); commit only `.env.example`.
- The frontend never holds DB credentials; it calls `api.`/`auth.` over HTTP.
- FastAPI verifies a Better Auth JWT via JWKS; `sub` is the canonical `user_id`.
- Two migration owners on one Postgres: Better Auth CLI (its tables) + Alembic
  (app tables). Keep their table sets distinct.
- Money is stored with original `amount` + `currency` and a converted
  `base_amount` + `exchange_rate`. Default currency is PHP.

## Task tracking (Linear)

**Linear is the source of truth for *what* to build.** Every feature, bug fix, or
change starts from a Linear issue. The issue — scope, acceptance criteria, links —
is the task contract, so work never depends on chat history. Combine the issue
(*what*) with the workspace's `AGENTS.md` (*how*).

- **Always work from a Linear issue, via the Linear MCP.** Read the issue first and
  treat it as the spec; keep it updated (move its state, link the PR) as you go.
- **Linear is required — do not proceed without it.** If the Linear MCP is not
  configured/authenticated, **stop and tell the developer to set it up**
  (see `docs/DEVELOPMENT.md` → Task tracking). Never guess the task or build from
  memory/chat alone.
- **Issue hygiene.** An issue must be self-sufficient: scope, acceptance criteria,
  target workspace (`frontend`/`api`/`auth`), and links to the relevant
  PRD/ARCHITECTURE sections.
- **Linking.** Put the issue ID in the branch and PR so Linear auto-links and
  transitions the issue: branch `type/<ISSUE-ID>-short-desc`
  (e.g. `feat/BUD-123-expense-filters`), PR title `type(scope): summary (BUD-123)`.

## Git workflow

`main` is **protected and is the production branch** — never commit or push to it
directly (GitHub blocks it; a PR is required). **Any merge into `main`
auto-triggers a deploy**, so only completed, release-ready code lands there.

Every change — a feature, a bug fix, or any edit — flows the same way:

1. **Work branch.** Branch off the current **release branch** (`release/X.Y`),
   e.g. `feat/expense-filters`, `fix/import-validation`.
2. **PR → release branch.** Open a PR from the work branch into the release
   branch; merge there after review.
3. **Release → `main`.** Only when the whole version is complete is the release
   branch merged into `main` — which tags the version and deploys.

So the path is always **work branch → release branch → `main`**. No code reaches
`main` except via a completed-version merge. Never open a PR straight to `main`
for a single feature/fix.

### Branch naming

- **Work branches** (in development): `type/<ISSUE-ID>-short-desc`, e.g.
  `feat/BUD-123-expense-filters`, `fix/BUD-145-import-validation`. The Linear
  issue ID lets Linear auto-link the branch/PR. Short-lived.
- **Release branch** (the one merged to `main`): **`release/X.Y`** (semver minor),
  e.g. `release/1.0`, `release/1.1`, `release/2.0`. Bump **MINOR** for a normal
  feature batch, **MAJOR** for breaking changes (e.g. a destructive data
  migration). Patch fixes fold into the current release rather than getting their
  own branch.
- On merge to `main`, tag the release `vX.Y.0` — this pairs with GitHub's
  auto-generated release notes if you enable them later.

### Commit messages

Use **Conventional Commits** for every commit *and* every PR title — one format
throughout. A release is not a special commit; it's the `release/X.Y → main`
merge, marked by the `vX.Y.0` tag.

```
<type>(<scope>): <imperative summary>   # ≤72 chars, lowercase, no trailing period

<optional body: what & why>
<optional footer: BREAKING CHANGE: …, refs #123>
```

- **Types:** `feat` (feature), `fix` (bug), `docs`, `refactor`, `perf`, `test`,
  `build` (deps/Docker/uv/pnpm/bun), `ci`, `chore` (maintenance), `style`.
- **Scope** = workspace or feature, e.g. `feat(frontend/expenses):`, `fix(api):`,
  `chore(infra):`. Encouraged in this monorepo.
- **One logical change per commit**, imperative mood ("add", not "added").
- **Bump signal:** `feat` → MINOR, `fix` → PATCH; a `!` after the type/scope or a
  `BREAKING CHANGE:` footer → MAJOR (drives the next `release/X.Y`).
- **PR titles use the same format** — work→release PRs are squash-merged, so the
  PR title becomes the release-branch commit and the release-note line.
- AI attribution is the model name only: a `Co-Authored-By:` trailer (no email)
  on commits. No tool/marketing footers in commits or PR descriptions.

Examples:

```
feat(api/expenses): add month filter to expense list
fix(frontend): prevent double submit on expense form
chore(infra): silence minio retry noise in createbuckets
feat(auth)!: change session cookie domain        # breaking → MAJOR
```

**Merge strategy:** squash-merge work → release (one clean commit per PR); use a
merge commit for release → `main`, then tag `vX.Y.0`.
