# Auth Service

Better Auth service for identity, sessions, JWT/JWKS, and organizations
(households). It runs on Bun and mounts Better Auth at `/api/auth/*`.

```sh
bun install
cp .env.example .env
bun run dev
```

Local service URL: http://localhost:4000

Schema is owned by the Better Auth CLI:

```sh
bun run schema:generate
bun run schema:migrate
```
