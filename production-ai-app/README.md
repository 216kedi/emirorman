# production-ai-app

Production-grade AI app template — every canonical file an AI codebase needs.

> Your AI app isn't just "a FastAPI wrapper around GPT."
>
> Real production AI systems need: retrieval pipelines, semantic caching, conversational memory, prompt versioning, agentic intelligence, safety guards, evaluation, and observability.

## Layout

```
production-ai-app/
├── app/                  FastAPI entry, config, schemas, containerised
├── components/           Custom retrieval: hybrid search + reranking
├── services/             Core business logic: pipeline, cache, memory, rewriting, routing
├── prompts/              Versioned, type-specific, hot-swappable
├── agents/               Intelligence layer + pluggable tools
├── security/             Three guard layers: input, content, output
├── evaluation/           Golden test set, offline + online pipelines
├── observability/        Per-stage tracing, feedback, cost breakdown
├── data/                 Raw → processed → index config
├── scripts/              Seed, migrate, healthcheck
├── frontend/             UI, containerised separately
├── tests/                Retrieval, cache, routing — CI-ready
├── docs/                 Architecture, API ref, deployment guide
├── claude/rules/         AI coding agent context, rules, project memory
├── CLAUDE.md
├── AGENTS.md
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Quickstart

```bash
docker compose up --build
```

- API: http://localhost:8000/health
- Frontend: http://localhost:8501

## Development

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest
```
