# CLAUDE.md

Project memory for AI coding agents working in this repo.

## What this is

A production-grade AI app template: RAG + agents + safety + evaluation + observability, containerised end-to-end.

## Where things live

- `app/` — FastAPI entry, config, request/response schemas.
- `components/` — Retrieval primitives.
- `services/` — Core business logic.
- `prompts/` — Versioned prompt templates.
- `agents/` — Self-correcting retrieval, decomposition, adaptive routing.
- `security/` — Input / content / output guards.
- `evaluation/` — Golden dataset + offline + online evaluators.
- `observability/` — Tracing, feedback, cost.
- `data/` — Raw → processed → index config.
- `scripts/` — Seed, migrate, healthcheck.
- `frontend/` — UI (containerised separately).
- `tests/` — Pytest.
- `docs/` — Architecture, API, deployment.

## Rules

See `claude/rules/code-style.md` and `claude/rules/testing.md`.

## Common tasks

- Run API locally: `uvicorn app.main:app --reload`
- Run tests: `pytest`
- Lint: `ruff check .`
- Evaluate: `python evaluation/offline_eval.py`
