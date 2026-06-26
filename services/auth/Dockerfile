# syntax=docker/dockerfile:1
# Better Auth service image (Bun). Used by infra/docker-compose.yml and built in
# CI (build.yml → ghcr.io).
FROM oven/bun:1
WORKDIR /app

# Install production deps first for layer caching.
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile --production

# Then the application code.
COPY . .

ENV NODE_ENV=production
EXPOSE 4000
# src/server.ts exports { port, fetch }, which Bun serves directly.
CMD ["bun", "run", "src/server.ts"]
