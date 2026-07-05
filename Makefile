# Expense Tracker — local development commands.
# Run from the repo root:  make <target>   (just `make` lists everything)

.DEFAULT_GOAL := help
.PHONY: help install up down logs reset api auth web worker

COMPOSE := docker compose -f infra/docker-compose.dev.yml

help: ## List available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "} {printf "  make %-8s %s\n", $$1, $$2}'

install: ## Install dependencies for frontend, auth, and api
	cd frontend && pnpm install
	cd services/auth && bun install
	cd services/api && uv sync

up: ## Start dev backing services (postgres, redis, minio)
	$(COMPOSE) up -d

down: ## Stop dev backing services (keeps data)
	$(COMPOSE) down

logs: ## Follow dev backing service logs
	$(COMPOSE) logs -f

reset: ## Stop the dev stack and DELETE all local data (volumes)
	$(COMPOSE) down -v

api: ## Run the FastAPI dev server with hot reload (:8000)
	cd services/api && uv run uvicorn app.main:app --reload

worker: ## Run the arq background worker
	cd services/api && uv run arq app.worker.settings.WorkerSettings

auth: ## Run the Better Auth (Bun/Hono) dev server
	cd services/auth && bun run dev

web: ## Run the Next.js frontend dev server (:3000)
	cd frontend && pnpm dev
