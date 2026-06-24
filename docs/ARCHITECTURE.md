# Architecture Document: Expense Tracker

## 1. Purpose and scope

This document describes how the Expense Tracker product (defined in the PRD) is built and run. It covers the tech stack, service topology, authentication, data, caching, background work, deployment, and cost posture. Product requirements live in the PRD; this document only describes implementation. The guiding constraint is "free or near-free until the product earns revenue," with one deliberate paid component (the application host).

## 2. Architecture at a glance

The browser loads the Next.js frontend from Vercel and calls the backend APIs on a paid application host. Cloudflare sits in front of both entry points, providing DNS, TLS, DDoS protection, WAF, and caching. The backend runs as a small set of Docker Compose services — Better Auth, FastAPI, PostgreSQL, Redis, and a background worker. Database backups and receipt-image uploads both use Cloudflare R2 (in separate buckets).

<div style="margin:14px 0;">
<svg width="100%" viewBox="0 0 720 540" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans, Arial, sans-serif">
<defs><marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="#73726c" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>

<rect x="288" y="20" width="144" height="44" rx="8" fill="#f1efe8" stroke="#888780" stroke-width="1"/>
<text x="360" y="40" text-anchor="middle" font-size="13" font-weight="bold" fill="#2c2c2a">Browser</text>
<text x="360" y="55" text-anchor="middle" font-size="10.5" fill="#5f5e5a">Next.js app + auth client</text>
<line x1="360" y1="64" x2="360" y2="92" stroke="#73726c" stroke-width="1.2" marker-end="url(#ar)"/>

<rect x="60" y="94" width="600" height="56" rx="10" fill="#faeede" stroke="#ba7517" stroke-width="1"/>
<text x="80" y="116" font-size="13" font-weight="bold" fill="#633806">Cloudflare edge</text>
<text x="80" y="134" font-size="10.5" fill="#854f0b">DNS · TLS (Full strict) · DDoS · WAF · CDN · optional Tunnel and Access</text>
<line x1="195" y1="150" x2="195" y2="188" stroke="#73726c" stroke-width="1.2" marker-end="url(#ar)"/>
<line x1="520" y1="150" x2="520" y2="188" stroke="#73726c" stroke-width="1.2" marker-end="url(#ar)"/>

<rect x="70" y="190" width="250" height="64" rx="10" fill="#f1efe8" stroke="#444441" stroke-width="1"/>
<text x="195" y="214" text-anchor="middle" font-size="13" font-weight="bold" fill="#2c2c2a">Vercel</text>
<text x="195" y="232" text-anchor="middle" font-size="10.5" fill="#5f5e5a">Next.js frontend — SSR,</text>
<text x="195" y="246" text-anchor="middle" font-size="10.5" fill="#5f5e5a">themes, static assets</text>

<rect x="380" y="190" width="300" height="258" rx="12" fill="#f7f3ec" stroke="#8a4b12" stroke-width="1"/>
<text x="396" y="210" font-size="12.5" font-weight="bold" fill="#8a4b12">Application host — Docker Compose</text>

<rect x="396" y="222" width="132" height="46" rx="8" fill="#eeedfe" stroke="#534ab7" stroke-width="1"/>
<text x="462" y="242" text-anchor="middle" font-size="12" font-weight="bold" fill="#3c3489">Better Auth</text>
<text x="462" y="257" text-anchor="middle" font-size="10" fill="#534ab7">Node · OAuth · JWKS</text>

<rect x="540" y="222" width="124" height="46" rx="8" fill="#e1f5ee" stroke="#0f6e56" stroke-width="1"/>
<text x="602" y="242" text-anchor="middle" font-size="12" font-weight="bold" fill="#085041">FastAPI</text>
<text x="602" y="257" text-anchor="middle" font-size="10" fill="#0f6e56">Python APIs</text>

<rect x="396" y="282" width="132" height="46" rx="8" fill="#e6f1fb" stroke="#185fa5" stroke-width="1"/>
<text x="462" y="302" text-anchor="middle" font-size="12" font-weight="bold" fill="#0c447c">PostgreSQL</text>
<text x="462" y="317" text-anchor="middle" font-size="10" fill="#185fa5">shared database</text>

<rect x="540" y="282" width="124" height="46" rx="8" fill="#fcebeb" stroke="#a32d2d" stroke-width="1"/>
<text x="602" y="302" text-anchor="middle" font-size="12" font-weight="bold" fill="#791f1f">Redis</text>
<text x="602" y="317" text-anchor="middle" font-size="10" fill="#a32d2d">cache · jobs · sessions</text>

<rect x="396" y="342" width="268" height="44" rx="8" fill="#f1efe8" stroke="#5f5e5a" stroke-width="1"/>
<text x="530" y="362" text-anchor="middle" font-size="12" font-weight="bold" fill="#2c2c2a">Background worker (arq)</text>
<text x="530" y="377" text-anchor="middle" font-size="10" fill="#5f5e5a">recurring expenses · FX refresh · backups</text>

<line x1="530" y1="448" x2="530" y2="478" stroke="#73726c" stroke-width="1.2" marker-end="url(#ar)"/>
<rect x="450" y="480" width="160" height="44" rx="8" fill="#faeede" stroke="#ba7517" stroke-width="1"/>
<text x="530" y="500" text-anchor="middle" font-size="12" font-weight="bold" fill="#633806">Cloudflare R2</text>
<text x="530" y="515" text-anchor="middle" font-size="10" fill="#854f0b">backups + receipt uploads</text>
</svg>
</div>

Subdomains keep the entry points separate behind Cloudflare: the marketing and app frontend on the apex/`app` domain (Vercel), the API on `api.`, and the auth service on `auth.`. All resolve through Cloudflare with the origins proxied.

## 3. Frontend — Next.js on Vercel

The frontend is a Next.js application deployed on Vercel's free (Hobby) tier, which auto-builds and deploys from Git. Next.js is Vercel's own framework, so SSR, routing, image handling, and the build pipeline work without adapter friction.

The UI is built with shadcn/ui (Radix UI primitives styled with Tailwind CSS). Components are copied into the codebase rather than pulled from a runtime dependency, so they can be themed and customized directly — which suits the per-workspace theming requirement (warm dark default). Tailwind's design tokens drive theme switching, and the accessible Radix primitives back the modal dialogs, menus, and form controls described in the PRD's UX requirements.

Responsibilities:

- Render the public landing page (server-rendered for SEO) and the authenticated dashboard.
- Hold the Better Auth client for sign-in, session state, and obtaining the JWT used to call FastAPI.
- Apply the active theme (warm dark default) resolved from the current workspace — personal or household.
- Perform reads/writes by calling the backend APIs over HTTPS; the browser never connects to the database directly.

Public configuration (API base URL, auth base URL, JWKS URL) is supplied through Vercel environment variables prefixed for client exposure; no secrets live in the frontend.

## 4. Edge and network — Cloudflare

Cloudflare's free plan fronts both Vercel and the application host, giving unmetered DDoS protection, Universal SSL, the managed WAF, CDN caching, and DNS at no cost.

- TLS mode is Full (strict) end to end; origins are reached over HTTPS.
- The application host's origin is shielded: either via Cloudflare proxy (orange-cloud) with the host firewall locked to Cloudflare IP ranges, or — preferred — via a Cloudflare Tunnel (`cloudflared`) so the host exposes no inbound ports and no public IP.
- A free rate-limiting rule guards the auth and import endpoints; Bot Fight Mode and Always-HTTPS/HSTS are enabled.
- Cloudflare Access (Zero Trust, free for up to 50 users) optionally gates internal/admin endpoints; the public landing page and normal app traffic stay open and rely on Better Auth.

When proxying Vercel through Cloudflare, DNS points at Vercel via CNAME with the record proxied, and SSL is set to Full (strict) to avoid redirect loops.

## 5. Backend services — application host

The backend runs on a paid application host as a single Docker Compose stack on one private network. Cloudflare sits in front; internal service-to-service traffic stays on the Compose network.

- `better-auth` (Node/TypeScript) — authentication, OAuth providers, the organization (household) model, and the JWKS endpoint.
- `fastapi` (Python) — all business APIs: expenses, categories, recurring rules, budgets, dashboards, Excel import/export.
- `postgres` — the single shared PostgreSQL database.
- `redis` — caching, rate limiting, Better Auth secondary storage, the job broker, and FX/idempotency caches.
- `worker` (Python, arq) — scheduled and queued background jobs.

Routing to the two HTTP services is handled by Cloudflare Tunnel ingress rules (hostname to local port) or a lightweight reverse proxy (Caddy/Traefik) if internal routing or local TLS is later needed.

## 6. Authentication and authorization

Better Auth is the authentication framework; because it is TypeScript, it runs as its own service rather than inside FastAPI. The two backends share one PostgreSQL database and are bridged with signed tokens.

- Providers: Google, GitHub, and Discord at launch (free to register); Microsoft, Apple, or Facebook can be added later (Apple requires a paid Apple Developer account; Facebook requires app review).
- Better Auth owns its schema — `users`, `accounts`, `sessions`, `verifications` — plus a `jwks` table from the JWT plugin, and `organizations`/`members`/`invitations` from the organization plugin. The service sets `usePlural: true`, so all Better Auth tables are plural.
- The organization plugin provides the household model: households are organizations, membership and roles (owner, member) are the org's members, and invites use the plugin's invite/accept lifecycle. "Household" is purely the user-facing label.
- Cross-service trust uses the JWT plugin and JWKS: the frontend obtains a JWT from Better Auth and sends it to FastAPI as a Bearer token; FastAPI verifies the RS256 signature against Better Auth's cached JWKS (via PyJWT's `PyJWKClient`), validating issuer, audience, and expiry, then trusts the `sub` claim as the user id. No per-request auth round-trip and no shared session logic.

Authorization is enforced in FastAPI: every query is scoped to the authenticated `user_id` and, for shared rows, to households the user belongs to with the role permitting the action. Native PostgreSQL row-level security can be layered as defense in depth.

## 7. Data layer

PostgreSQL is the single source of truth. Application tables own their data and reference identity by id; identity and household structures are owned by Better Auth.

- Application tables (`user_categories`, `expenses`, `recurring_expenses`, `user_monthly_settings`) reference the Better Auth `users.id` as `user_id`, and reference a household by storing the `organizations.id` in their `household_id` column.
- Migrations have two owners on one database: the Better Auth CLI manages its tables; Alembic manages the application tables. Their table sets are kept distinct to avoid collisions.
- Theme and base-currency preferences: per-user values extend the Better Auth user record; per-household values extend the organization record. No separate preferences table is required.
- Currency: each expense stores its entered `amount` and `currency`, plus the `base_amount` and `exchange_rate` used for conversion, so summaries aggregate into the workspace's base currency.

## 8. Caching strategy

Caching is layered, with each layer owning a different concern:

- Next.js — the primary application cache: `unstable_cache`/`use cache` around data reads, ISR/`revalidate` for time- and tag-based invalidation, and `cache()` for per-request memoization. Caching is opt-in (Next.js no longer caches `fetch` by default).
- Cloudflare CDN — caches static assets and any explicitly cacheable GET responses, purged on write.
- Redis — server-side query-result caching, FX-rate cache, idempotency keys for Excel imports, rate-limit counters, and Better Auth secondary storage.

## 9. Background jobs and scheduling

A single arq worker (Redis-backed) runs scheduled and queued work:

- Generate recurring-expense occurrences into the correct months.
- Refresh exchange rates from the chosen FX source and cache them in Redis.
- Run database backups on a schedule.
- Process any deferred or heavy work offloaded from request handlers (e.g. large imports).

## 10. Multi-currency handling

A scheduled job pulls exchange rates from a free FX source once per day and caches them in Redis. When an expense is recorded in a non-base currency, the API stores the original amount and currency alongside the converted base amount and the rate applied, so historical totals remain stable even if rates later change. Each workspace (user or household) has a base currency used for all summaries.

## 11. Backups and disaster recovery

The application host is a single point of failure, so backups are off-box. A scheduled `pg_dump` is pushed to Cloudflare R2 (10 GB free), with roughly 7–30 days of retention. Restores are tested periodically. Better Auth and application schemas are captured together since they share one database.

## 12. File storage (Cloudflare R2)

Receipt images are stored in Cloudflare R2 (S3-compatible, no egress fees), in a **separate private bucket** from the database backups. The database holds only the object key, never the bytes.

Uploads and downloads use **presigned URLs**, so file data never flows through FastAPI:

1. The browser asks FastAPI for an upload URL for a given expense.
2. FastAPI checks the caller is allowed to attach to that expense (same ownership and household rules as the row), then returns a short-lived presigned PUT URL scoped to one object key, with content-type and size limits applied.
3. The browser uploads the image **directly to R2**; the bytes never touch the application host.
4. FastAPI records the object key in `expense_attachments`.
5. To view a receipt, the browser requests a short-lived presigned GET URL, again issued only after the same authorization check.

The bucket is private with no public read access, so a leaked key is useless without a freshly signed, expiring URL. R2 is reached with any S3 SDK (for example `boto3`) using R2 credentials held only on the application host. Because R2 is already used for backups, this adds a bucket rather than a new dependency.

## 13. CI/CD and deployment

- Frontend: Vercel builds and deploys automatically only on push to the main branch; branch and pull request preview deployments are disabled in `frontend/vercel.json`.
- Backend: GitHub Actions builds the service images and pushes them to GitHub Container Registry (`ghcr.io`, free); the host pulls and restarts the affected services (via a pull-based updater or an SSH deploy step).
- Database migrations run as a deploy step: Better Auth CLI for its tables, Alembic for application tables.

## 14. Secrets and configuration

- Backend secrets live in the host environment (`.env`, never committed): `BETTER_AUTH_SECRET`, OAuth client IDs and secrets, the PostgreSQL and Redis connection URLs, and the R2 access keys used to sign upload/download URLs.
- Frontend receives only public configuration through Vercel environment variables: the API, auth, and JWKS base URLs.
- OAuth client secrets and signing keys are rotated through the host environment; the JWKS public keys are served by Better Auth for verification.

## 15. Cross-origin, cookies, and CORS

The frontend (Vercel domain) and APIs (`api.`/`auth.` behind Cloudflare) are different origins. Because FastAPI authentication is Bearer-token based rather than cookie based, cross-site cookie handling is largely avoided. FastAPI's CORS policy allows the frontend origin, and Better Auth's `trustedOrigins` is set to match. Personal or sensitive data is never placed in URL query strings.

## 16. Observability and uptime

Kept light for a small user base: Cloudflare analytics for edge traffic, container logs on the host, and a free external monitor (Uptime Robot or Better Stack) checking the `api.` and `auth.` endpoints. A heavier metrics stack (e.g. Prometheus/Grafana) can be added later if needed.

## 17. Cost posture

- Free: Vercel Hobby (frontend), Cloudflare (edge), Cloudflare R2 within 10 GB (backups + receipt uploads), GitHub Actions and `ghcr.io` (CI), external uptime monitor, and OAuth app registrations for Google/GitHub/Discord.
- Paid: the application host (already in place) and the domain name.
- Watch items: Vercel's Hobby tier is intended for non-commercial use, so a move to Pro is expected once the product earns revenue; Apple Sign In adds an annual Apple Developer fee if enabled.

## 18. Security considerations

- The origin host is shielded behind Cloudflare (preferably a Tunnel) so it has no exposed ports or public IP.
- All traffic is HTTPS end to end with Full (strict) TLS.
- Authorization is enforced server-side per user and per household role, optionally reinforced by PostgreSQL row-level security.
- Secrets are confined to the host environment and never reach the browser or the repository.
- Rate limiting protects authentication and import endpoints; the WAF and Bot Fight Mode filter common abuse.
- Receipt storage is private: the R2 bucket has no public read access, file bytes never pass through the application host, and every upload or view requires a short-lived presigned URL issued only after an authorization check.

## 19. Future considerations

- Migrate Vercel to Pro and revisit Supabase/managed Postgres only if scale or operations justify it.
- Add teams within households (Better Auth supports team tables) if sub-grouping is needed.
- Introduce a richer theme set and per-user overrides within a household if demand appears.
- Add server-side aggregation or read replicas if expense histories grow large.
