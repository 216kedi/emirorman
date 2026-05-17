# CLAUDE.md

Project memory for AI coding agents.

## What this is

A production RAG + agent platform (2026 stack): async FastAPI + Qdrant + Redis +
Anthropic (with prompt caching) + Instructor for typed outputs + MCP server +
structlog correlated logging + three-layer safety.

## Layout

- `app/` — FastAPI: `main.py`, `config.py`, `models.py`, `logging.py`, `errors.py`, `middleware.py`, `dependencies.py`, `routes/`.
- `components/` — Retrieval primitives: `hybrid_retriever.py` (dense + BM25 + RRF), `reranker.py` (LLM scorer).
- `services/` — Business logic:
  - `llm/` — provider abstraction (`base.py`, `anthropic_client.py`, `openai_client.py`).
  - `vector_store/` — `qdrant.py` async wrapper.
  - `embeddings.py`, `rag_pipeline.py`, `semantic_cache.py`, `conversation.py`,
    `query_rewriter.py`, `query_router.py`, `mcp_server.py`.
- `prompts/` — `templates.py` (cache-marked), `registry.py`.
- `agents/` — `document_grader.py`, `query_decomposer.py`, `adaptive_router.py`, `tools/`.
- `security/` — `input_guard.py`, `content_filter.py`, `output_filter.py`.
- `evaluation/` — golden dataset, offline + online eval, `eval_results/`.
- `observability/` — `tracer.py`, `feedback.py`, `cost_tracker.py`.
- `data/` — raw → processed → index_config.
- `scripts/` — `seed.py`, `migrate.py`, `healthcheck.py`.
- `frontend/` — Streamlit, separate container.
- `tests/` — pytest-asyncio.
- `docs/` — architecture, API, deployment.

## Rules

See `claude/rules/code-style.md` and `claude/rules/testing.md`.

## Common tasks

```bash
uv sync                          # install
uv run uvicorn app.main:app      # run API
uv run python scripts/migrate.py # create Qdrant collection
uv run python scripts/seed.py    # seed initial docs
uv run pytest                    # tests
uv run ruff check .              # lint
uv run python -m services.mcp_server  # run MCP server
```

## Conventions

- All I/O is async. No sync `requests` in service layer (frontend exempt).
- Every request gets a `trace_id`; bound to `structlog` contextvars by middleware.
- LLM calls go through `services.llm.base.LLMClient`. Never import `anthropic` / `openai` directly in business logic.
- Prompts live in `prompts/` and are versioned; mark cacheable prompts with `cache_control="ephemeral"`.
- Safety guards run on every request — input → content → output. Don't bypass.
- New module under `services/` or `components/` → add a sibling test under `tests/`.
