# production-ai-app

Production-grade RAG + agent platform — 2026 stack.

> Not just "a FastAPI wrapper around an LLM."
>
> Real production AI systems need: hybrid retrieval, semantic caching,
> conversational memory, prompt versioning + caching, agentic intelligence,
> safety guards, evaluation, and observability — all async, all typed,
> all wired together.

## Stack

- **API:** FastAPI (async, ORJSON, lifespan, correlation middleware)
- **LLM:** Anthropic (with prompt caching) + OpenAI, via a `Protocol` abstraction
- **Typed outputs:** Instructor (Pydantic schemas from LLMs)
- **Retrieval:** Qdrant (async) + BM25, fused with Reciprocal Rank Fusion
- **Reranking:** LLM-as-judge scorer
- **Cache:** Redis-backed semantic cache (cosine over query embeddings)
- **Memory:** Redis-backed multi-turn conversation store
- **Tooling exposure:** MCP server (`services/mcp_server.py`) for Claude Desktop / Cursor / etc.
- **Streaming:** SSE via `sse-starlette`
- **Logging:** structlog with `trace_id` correlation
- **Package mgmt:** uv (lockfile-based, fast)
- **Container:** multi-stage, non-root, distroless-style runtime

## Layout

```
production-ai-app/
├── app/                  FastAPI: routes, config, middleware, DI, errors
├── components/           Hybrid retrieval, reranker
├── services/             LLM clients, vector store, RAG pipeline, cache, MCP
├── prompts/              Versioned, cache-marked templates
├── agents/               Self-correcting retrieval + pluggable tools
├── security/             Input / content / output guards
├── evaluation/           Golden set + offline/online evaluators
├── observability/        Tracer, feedback, cost
├── data/                 raw → processed → index_config
├── scripts/              seed, migrate, healthcheck
├── frontend/             Streamlit UI
├── tests/                pytest-asyncio
└── docs/                 architecture, API, deployment
```

## Quickstart

```bash
cp .env.example .env  # fill in API keys
docker compose up --build
```

Then:
```bash
docker compose exec api python scripts/migrate.py
docker compose exec api python scripts/seed.py
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is MCP?"}'
```

Stream tokens:
```bash
curl -N -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query":"Explain hybrid retrieval briefly."}'
```

## Development

```bash
uv sync --group dev
uv run uvicorn app.main:app --reload
uv run pytest
uv run ruff check .
```

## MCP server

Expose this app to any MCP client:
```bash
uv run python -m services.mcp_server
```
