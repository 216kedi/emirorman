# production-ai-app

[![CI](https://github.com/your-org/production-ai-app/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/production-ai-app/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Production-grade RAG + ajan platformu — 2026 stack.

> "AI uygulamanız sadece 'GPT etrafına sarılmış bir FastAPI' değil."
>
> Gerçek production AI sistemleri şunlara ihtiyaç duyar: hibrit retrieval,
> graph genişleme, late-interaction reranking, semantik önbellek,
> çok katmanlı bellek, versiyonlu + optimize edilmiş prompt'lar,
> ajan zekası, güvenlik guard'ları, değerlendirme pipeline'ı ve gözlemlenebilirlik.

---

## Mimari

```
İstek
  │
  ▼
[CorrelationMiddleware]  →  trace_id bağlanır
  │
  ▼
[InputGuard]             →  injection / PII / uzunluk kontrolü
  │
  ▼
[QueryRouter]            →  simple_lookup | rag | agentic   (Instructor typed)
  │
  ▼
[QueryRewriter]          →  retrieval için yeniden yazar
  │
  ▼
[HybridRetriever]        →  Qdrant (dense) + BM25 (sparse) + RRF füzyon
  │
  ▼
[GraphRetriever]         →  bilgi grafiği komşu genişleme
  │
  ▼
[LateInteractionReranker]→  ColBERT tarzı MaxSim
  │
  ▼
[ContentFilter]          →  PII redaction
  │
  ▼
[LLM]                    →  Anthropic (prompt caching) veya OpenAI
  │
  ▼
[OutputFilter]           →  grounding + refusal kontrolü
  │
  ▼
[SemanticCache.put]      →  yanıtı önbelleğe al
  │
  ▼
Yanıt
```

## Stack

| Katman | Teknoloji |
|---|---|
| API | FastAPI async, ORJSON, SSE, slowapi |
| LLM | Anthropic (prompt caching) + OpenAI; Protocol abstraction |
| Typed outputs | Instructor (Pydantic AI) |
| Retrieval | Qdrant + BM25 → RRF → GraphRAG → ColBERT MaxSim |
| Önbellek | Redis semantic cache |
| Bellek | Episodic + Semantic + Procedural (Redis) |
| MCP | FastMCP sunucu (Claude Desktop / Cursor) |
| Prompt opt. | DSPy (BootstrapFewShot + MIPROv2) |
| Güvenlik | Input / Content / Output guard zinciri |
| Eval | RAGAS + LLM-as-judge + Recall@k / nDCG + Trajectory + Red-team |
| Observability | structlog + OTel + Langfuse + Prometheus + Grafana |
| Paket | uv (lockfile, PEP 735) |
| Container | Multi-stage Dockerfile, non-root, healthcheck |

## Hızlı başlangıç

```bash
git clone https://github.com/your-org/production-ai-app
cd production-ai-app
cp .env.example .env   # ANTHROPIC_API_KEY ve OPENAI_API_KEY doldurun
make dev               # bağımlılıkları kur
docker compose up -d
make migrate           # Qdrant koleksiyonu oluştur
make seed              # örnek dökümanları indeksle
```

**API:** http://localhost:8000/docs
**Frontend:** http://localhost:8501
**Metrics:** http://localhost:8000/metrics

### Örnek sorgu

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Hibrit retrieval nasıl çalışır?"}'
```

### SSE streaming

```bash
curl -N -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "MCP nedir?"}'
```

### MCP sunucusu (Claude Desktop / Cursor)

```bash
make mcp
```

## Geliştirme

```bash
make test           # testler
make test-cov       # coverage raporu
make lint           # ruff lint + format
make eval           # offline evaluation (ANTHROPIC_API_KEY gerekli)
make red-team       # güvenlik guard red-team
make optimize-prompts  # DSPy prompt optimizasyonu
```

## Klasör yapısı

```
production-ai-app/
├── app/              FastAPI: routes, config, auth, middleware, DI
├── components/       Hibrit retrieval, GraphRAG, ColBERT reranker
├── services/
│   ├── llm/          Anthropic + OpenAI istemcileri
│   ├── vector_store/ Qdrant async wrapper
│   ├── memory/       Episodic + Semantic + Procedural
│   └── ...           RAG pipeline, cache, router, DSPy optimizer, MCP
├── prompts/          Versiyonlu şablonlar, DSPy modülleri
├── agents/           Document grader, decomposer, router, tools, trajectory
├── security/         Input / Content / Output guard'ları
├── evaluation/       RAGAS, LLM-as-judge, retrieval metrikleri, red-team
├── observability/    OTel, Langfuse, Prometheus, maliyet takibi
├── data/             Ham → işlenmiş → indeks config
├── scripts/          seed, migrate, healthcheck
├── frontend/         Streamlit UI
├── tests/            pytest-asyncio (30+ test)
├── docs/             Mimari, API, deployment
└── .github/          CI/CD, eval nightly, issue şablonları, Dependabot
```

## Katkı

[CONTRIBUTING.md](CONTRIBUTING.md) dosyasına bakın.

## Lisans

[MIT](LICENSE)
