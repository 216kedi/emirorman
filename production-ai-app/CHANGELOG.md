# Changelog

Bu projedeki tüm önemli değişiklikler burada belgelenir.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versiyonlama: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [Unreleased]

### Eklendi
- GraphRAG: Redis tabanlı knowledge graph, BFS komşu genişleme
- Late-interaction (ColBERT tarzı) reranker, MaxSim token-window yaklaşımı
- 3 katmanlı memory: episodic, semantic, procedural (mem0 tarzı)
- DSPy prompt optimizer (BootstrapFewShot + MIPROv2)
- Agent trajectory evaluator (strateji / verimlilik / kalite)
- TrajectoryRecorder context manager

---

## [0.2.0] — 2026-05-17

### Eklendi
- **Phase 1 — Working skeleton**
  - Async FastAPI, lifespan, ORJSON, CorrelationMiddleware
  - LLM provider abstraction: Anthropic (prompt caching) + OpenAI, Protocol tabanlı
  - Instructor ile typed routing (Pydantic schema)
  - Qdrant async client + BM25 + Reciprocal Rank Fusion hybrid retrieval
  - LLM-as-judge reranker
  - Redis semantic cache (cosine over query embeddings)
  - Redis multi-turn conversation store
  - Gerçek input/content/output güvenlik guard'ları
  - SSE streaming endpoint (`POST /query/stream`)
  - MCP server (`rag_query`, `search_knowledge_base` tool'ları)
  - structlog + trace_id contextvars
  - Custom exception hierarchy + global error handler
  - uv + PEP 735 dependency groups, ruff lint config
  - Multi-stage Dockerfile (non-root, healthcheck)
  - docker-compose healthcheck gate'leri

- **Phase 2 — Production hardening**
  - CI/CD: lint → test → security scan → Docker build + SBOM
  - Release workflow: multi-arch GHCR push, GitHub Release
  - pre-commit: ruff, detect-secrets, trailing-whitespace
  - Makefile (12 hedef)
  - OpenTelemetry tracing (OTLP + Console dev)
  - Langfuse client (lazy-init, trace + score)
  - Prometheus metrics: 7 counter/histogram/gauge
  - `/metrics` + `/metrics/process` endpoint'leri
  - slowapi rate limiting (dakikada 60, ayarlanabilir)
  - API key auth (`x-api-key`, timing-safe compare)
  - `/feedback` endpoint → Langfuse score
  - Per-model maliyet tablosu + Prometheus counter'lar
  - SECURITY.md tehdit modeli

- **Phase 3 — Eval & quality**
  - Retrieval metrikleri: Recall@k, Precision@k, MRR, nDCG (sıfır bağımlılık)
  - LLM-as-judge: faithfulness, relevance, correctness (paralel)
  - RAGAS pipeline entegrasyonu (4 metrik)
  - Offline eval runner (Rich tablo + JSON çıktı)
  - Online monitor (%5 örnekleme, Langfuse, kalite alarmı)
  - Red-team framework: 6 saldırı kategorisi, LLM probe üretici
  - Synthetic QA üretici (dökümanlardan)
  - Grafana dashboard (7 panel)
  - Nightly eval CI job

## [0.1.0] — 2026-05-17

### Eklendi
- İlk proje iskeleti (klasör yapısı, stub modüller)
- Tüm `__init__.py` paket dosyaları
- Temel FastAPI giriş noktası
- docker-compose (Qdrant, Redis)
- pyproject.toml (uv tabanlı)
- README, CLAUDE.md, AGENTS.md

[Unreleased]: https://github.com/your-org/production-ai-app/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/your-org/production-ai-app/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/your-org/production-ai-app/releases/tag/v0.1.0
