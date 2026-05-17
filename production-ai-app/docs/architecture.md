# Architecture

High-level overview of the production AI app:

- **app/** — FastAPI entry, config, schemas, container.
- **components/** — Retrieval primitives (hybrid search, reranker).
- **services/** — Core business logic (RAG pipeline, semantic cache, conversation, query rewriting, routing).
- **prompts/** — Versioned, hot-swappable templates and registry.
- **agents/** — Intelligence layer: self-correcting retrieval, decomposition, adaptive routing, tools.
- **security/** — Three guard layers: input, content, output.
- **evaluation/** — Golden dataset, offline + online evaluation harness.
- **observability/** — Tracing, feedback capture, cost tracking.
- **data/** — Raw → processed → index config.
- **scripts/** — Seed, migrate, healthcheck.
- **frontend/** — UI, containerised separately.
- **tests/** — Retrieval, cache, routing.

## Request flow

`client → app.main → security.input_guard → services.query_router → services.rag_pipeline → components.hybrid_retriever → components.reranker → security.content_filter → llm → security.output_filter → response`
