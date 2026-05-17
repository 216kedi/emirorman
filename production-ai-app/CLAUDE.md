# CLAUDE.md

AI kodlama ajanları için proje hafızası.

## Bu nedir?

2026 stack'i üzerine inşa edilmiş production-grade RAG + ajan platformu:

- **API:** Async FastAPI, ORJSON, lifespan, CorrelationMiddleware
- **LLM:** Anthropic (prompt caching) + OpenAI; `Protocol` tabanlı abstraction + Instructor typed outputs
- **Retrieval:** Qdrant (async) + BM25 + RRF hybrid → GraphRAG genişleme → ColBERT late-interaction reranker
- **Memory:** Episodic + Semantic + Procedural (3 katman, Redis tabanlı)
- **Cache:** Redis semantic cache (cosine over query embeddings)
- **Streaming:** SSE (`POST /query/stream`)
- **MCP:** `services/mcp_server.py` → Claude Desktop / Cursor entegrasyonu
- **Prompt optimization:** DSPy (BootstrapFewShot + MIPROv2)
- **Safety:** Input → Content → Output guard zinciri
- **Eval:** RAGAS + LLM-as-judge + retrieval metrikleri + trajectory eval + red-team
- **Observability:** structlog + OTel + Langfuse + Prometheus + Grafana dashboard
- **Paket yönetimi:** uv, PEP 735 dependency groups

## Klasör yapısı

```
app/              FastAPI: routes/, config, models, logging, errors, middleware, auth, dependencies
components/       hybrid_retriever, reranker (LLM-as-judge), graph_retriever (GraphRAG), late_interaction (ColBERT)
services/
  llm/            base (Protocol), anthropic_client (prompt caching), openai_client
  vector_store/   qdrant.py (async)
  memory/         episodic, semantic, procedural, manager (MemoryManager)
  embeddings.py   EmbeddingService (OpenAI)
  rag_pipeline.py end-to-end pipeline (safety → route → rewrite → retrieve → rerank → generate)
  semantic_cache.py Redis cosine cache
  conversation.py multi-turn Redis store
  query_rewriter.py LLM rewrite
  query_router.py   Instructor typed routing
  dspy_optimizer.py prompt optimization
  mcp_server.py   FastMCP sunucu
prompts/          templates.py (versiyonlu, cacheable), registry.py, dspy_modules.py
agents/
  document_grader.py, query_decomposer.py, adaptive_router.py
  tools/          vector_search, web_search, code_search
  trajectory/     recorder.py (TrajectoryRecorder)
security/         input_guard, content_filter, output_filter
evaluation/
  metrics.py        Recall@k, Precision@k, MRR, nDCG
  llm_judge.py      faithfulness, relevance, correctness
  ragas_eval.py     RAGAS pipeline
  offline_eval.py   golden dataset runner (Rich tablo)
  online_monitor.py live örnekleme + Langfuse alarm
  red_team.py       probe üretici + bypass raporu
  synthetic_data.py LLM tabanlı QA üretici
  trajectory_eval.py ajan adım değerlendirmesi
  dashboards/       grafana.json (7 panel)
observability/    tracer (OTel), langfuse_client, metrics (Prometheus), feedback, cost_tracker
data/             raw/, processed/, index_config/
scripts/          seed.py, migrate.py, healthcheck.py
frontend/         Streamlit + Dockerfile
tests/            pytest-asyncio, 30+ birim testi
docs/             architecture.md, api-reference.md, deployment.md
claude/rules/     code-style.md, testing.md
```

## Sık kullanılan komutlar

```bash
make dev              # bağımlılık kur + pre-commit etkinleştir
make api              # sıcak-yeniden-yüklemeli API sunucusu
make test             # testleri çalıştır
make test-cov         # coverage raporu
make lint             # ruff lint + format kontrolü
make migrate          # Qdrant koleksiyonu oluştur
make seed             # örnek dökümanları ekle
make mcp              # MCP sunucusunu başlat
make eval             # offline evaluation
make red-team         # guard red-team
make synthetic        # sentetik QA üretici
make optimize-prompts # DSPy BootstrapFewShot
make docker-up        # tam stack
```

## Kritik kurallar

1. Tüm I/O **async** — servis katmanında sync `requests` yasak (frontend hariç)
2. LLM çağrıları yalnızca `services.llm.base.LLMClient` üzerinden — `anthropic`/`openai` direkt import edilmez
3. Yeni prompt → versiyonlu `prompts/templates.py`, `registry.py`'ye kayıtlı; cacheable olanlar `cache_control="ephemeral"`
4. Safety guard zinciri (**input → content → output**) her istekte çalışır — bypass edilmez
5. Yeni `services/` veya `components/` modülü → `tests/` altında kardeş test dosyası
6. Her modül `trace_id` kullanır — `structlog.contextvars` middleware tarafından bağlanır
7. Gizli değerler yalnızca `app/config.py` üzerinden env'den yüklenir — hardcode yasak
