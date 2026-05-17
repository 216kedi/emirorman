.DEFAULT_GOAL := help
PYTHON        := uv run python
PYTEST        := uv run pytest
RUFF          := uv run ruff

.PHONY: help install dev lint format test test-cov migrate seed mcp docker-up docker-down eval red-team synthetic clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install production deps with uv
	uv sync

dev: ## Install all deps including dev group
	uv sync --group dev
	uv run pre-commit install

lint: ## Run ruff lint + format check
	$(RUFF) check .
	$(RUFF) format --check .

format: ## Auto-fix lint + format in place
	$(RUFF) check --fix .
	$(RUFF) format .

test: ## Run tests
	$(PYTEST) -q

test-cov: ## Run tests with coverage report
	$(PYTEST) --cov --cov-report=term-missing --cov-report=html -q

migrate: ## Create / migrate Qdrant collections
	$(PYTHON) scripts/migrate.py

seed: ## Seed Qdrant with sample documents
	$(PYTHON) scripts/seed.py

mcp: ## Start the MCP server
	$(PYTHON) -m services.mcp_server

api: ## Run dev API server with hot-reload
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-up: ## Start full stack with docker compose
	docker compose up --build -d

docker-down: ## Stop docker compose stack
	docker compose down -v

eval: ## Run offline evaluation (requires running API + ANTHROPIC_API_KEY)
	$(PYTHON) -m evaluation.offline_eval

red-team: ## Run red-team probes against guardrails
	$(PYTHON) -m evaluation.red_team

synthetic: ## Generate synthetic golden QA pairs from docs/
	$(PYTHON) evaluation/synthetic_data.py

clean: ## Remove caches and build artefacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage coverage.xml
