<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# frontend — Agent Guide

> **Two separate concerns — don't conflate them:**
> 1. **Framework correctness (the block above).** This repo runs **Next.js 16**,
>    whose APIs differ from older versions. For anything about *how Next works*
>    (routing, `app/` files, caching, server/client components, config), trust the
>    bundled docs in `node_modules/next/dist/docs/` over your training data.
> 2. **Our design pattern (everything below).** This is *how we organize our own
>    code* in this workspace. It is intentional and authoritative — the "distrust
>    your training data" rule from concern #1 does **not** apply here; follow it as
>    written. The docs tell you the correct Next API; this guide tells you where
>    code goes and how we structure it. Both apply, to different questions.

Next.js (App Router) on Vercel. **pnpm** · **shadcn/ui** (Radix + Tailwind) ·
**TanStack Query** (server state) · **Zustand** (client state) ·
**react-hook-form + zod** (forms) · **Better Auth** client · **next-themes**.

The repo-wide layout is in `docs/STRUCTURE.md`; it stops at this folder's
boundary — the rules here win for anything under `frontend/`.

## Architecture: feature-first

Group code by **domain feature**, not by file type. Routes stay thin and compose
features; all real logic lives inside a feature. Do not grow a flat `components/`
or `lib/` junk drawer.

```text
app/                  # App Router = ROUTING ONLY (thin; composes features)
  layout.tsx          #   root layout → <Providers/>
  page.tsx            #   public landing (Server Component, SEO)
  (auth)/             #   sign-in / sign-up
  (app)/              #   authenticated area
    layout.tsx        #   auth guard + app shell (nav, workspace switcher)
    dashboard/page.tsx

features/<feature>/   # ⭐ one folder per domain (expenses, categories, budget,
  components/         #     recurring, dashboard, households, currency, import-export)
  api/                #   TanStack hooks: queries.ts + mutations.ts
  schemas.ts          #   zod schemas → z.infer for types
  store.ts            #   (optional) Zustand slice for this feature's UI state
  index.ts            #   PUBLIC BARREL — the only entry other code may import

components/
  ui/                 # shadcn primitives (CLI-generated; compose, don't fork)
  shared/             # cross-feature app components (AppShell, EmptyState, …)

lib/
  api-client.ts       # fetch wrapper: base URL + attaches Bearer JWT
  auth-client.ts      # Better Auth client (+ organization plugin)
  query-client.ts     # QueryClient factory + defaults
  query-keys.ts       # ONE central query-key factory
  format.ts           # currency/date formatting (en-PH, multi-currency)
  utils.ts            # cn(), small helpers

providers/            # ThemeProvider, QueryProvider, WorkspaceProvider (compose in app/layout)
stores/               # cross-cutting Zustand stores (e.g. active workspace)
hooks/                # cross-cutting hooks only (useDebounce, …)
styles/               # globals.css + themes/ (token sets, warm-dark default)
```

## Rules

**Boundaries.** Import another feature only through its `index.ts` barrel — never
a deep path. A feature is a black box. `@/features/*` is a tsconfig path alias.

**Server state = TanStack Query, always.** Never copy server data into Zustand or
`useState`. Each feature's `api/queries.ts` exposes `useXxx()` read hooks and
`api/mutations.ts` exposes mutation hooks. **Mutations invalidate keys** from
`lib/query-keys.ts` — that is how dashboard totals refresh instantly after
create/edit/delete/import (PRD §5, §7.8).

**Client state = Zustand**, for UI/ephemeral state only (active personal/household
workspace, filters, modal/sheet open state). Keep stores small and colocated:
cross-cutting → `stores/`, feature-local → `features/x/store.ts`.

**Data fetching boundary.** The `(app)` area is Client Components driven by
TanStack Query. Server Components are for the **public landing only** (SEO). No
RSC prefetch/hydration dance unless a page later proves it needs it.

**Forms = react-hook-form + zod + shadcn `<Form>`.** The feature's `schemas.ts`
is the single source of truth; derive types with `z.infer`. Validate before
submit (PRD §11).

**shadcn.** Add primitives with `pnpm dlx shadcn@latest add <name>` → they land in
`components/ui/`. Compose them in feature components; don't edit primitives by
hand. Theming is Tailwind tokens + `next-themes`, applied per workspace (PRD §8).

**Auth + API.** `lib/auth-client.ts` owns the Better Auth session/JWT.
`lib/api-client.ts` attaches the Bearer JWT to every call to `api.` — components
never build fetch calls or hold credentials directly.

**Naming.** kebab-case filenames, PascalCase component exports, co-located
`*.test.tsx` (Vitest + RTL) when tests are added.

## Recipe — adding a feature

1. `features/<name>/schemas.ts` — zod schemas first (shape + validation).
2. `features/<name>/api/queries.ts` + `mutations.ts` — hooks using `api-client`
   and keys from `lib/query-keys.ts`; mutations invalidate the right keys.
3. `features/<name>/components/` — UI composed from `components/ui/`.
4. `features/<name>/index.ts` — export only the public surface.
5. Wire a thin route in `app/(app)/<name>/page.tsx`.
6. Add new shadcn primitives via the CLI as needed.

## Commands

Run the app from the **repo root** via the Makefile (the canonical entry; it just
wraps pnpm). Use **pnpm inside `frontend/`** for frontend-only tooling the
Makefile doesn't cover.

```
make web                          # from repo root — start dev server (= pnpm dev) :3000

pnpm lint                         # eslint
pnpm typecheck                    # tsc --noEmit
pnpm test                         # vitest (when tests exist)
pnpm dlx shadcn@latest add <name> # add a shadcn primitive
```

Rule of thumb: **Makefile = run services / cross-workspace orchestration; pnpm =
frontend-specific tasks.** Env: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_AUTH_URL`
(see `.env.example`) — public config only, never secrets.
