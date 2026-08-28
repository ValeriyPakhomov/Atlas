.DEFAULT_GOAL := help
.PHONY: help bootstrap lint format typecheck test check api worker db-up db-down db-test-up db-test-down migrate downgrade clean

help: ## List available targets
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  %-12s %s\n", $$1, $$2}'

bootstrap: ## Create .venv, install dev dependencies, seed .env
	./scripts/bootstrap.sh

lint: ## Ruff lint
	uv run ruff check .

format: ## Ruff format (writes)
	uv run ruff format .

typecheck: ## mypy --strict over packages, apps and tests
	uv run mypy packages apps tests

test: ## pytest
	uv run pytest

check: ## Everything CI runs
	./scripts/check.sh

api: ## Run the API locally on :8000
	uv run uvicorn atlas_api.main:app --reload --port 8000

worker: ## Run the worker entrypoint once
	uv run python -m atlas_worker.main

db-up: ## Start the local PostgreSQL database
	docker compose up -d db

db-down: ## Stop local infrastructure
	docker compose down

db-test-up: ## Start the isolated PostgreSQL test database
	docker compose up -d db-test

db-test-down: ## Stop and remove the isolated test database
	docker compose stop db-test
	docker compose rm -f db-test

migrate: ## Upgrade the configured database to the latest schema
	uv run alembic upgrade head

downgrade: ## Downgrade the configured database by one revision
	uv run alembic downgrade -1

clean: ## Remove caches and the virtualenv
	rm -rf .venv .pytest_cache .ruff_cache .mypy_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
