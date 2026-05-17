# Mimari

## Genel bakış

production-ai-app; retrieval, bellek, güvenlik ve değerlendirmeyi tek çatı altında birleştiren production-grade bir RAG + ajan platformudur.

## İstek akışı

```
İstemci
  │  POST /query  (x-api-key, x-trace-id)
  ▼
CorrelationMiddleware       trace_id üretir, structlog'a bağlar
  │
  ▼
slowapi RateLimiter         dakikada N istek (ayarlanabilir)
  │
  ▼
InputGuard                  regex injection, PII, uzunluk
  │
  ▼
SemanticCache.get           Redis cosine — cache hit → direkt yanıt
  │ miss
  ▼
MemoryManager.before_query  episodic + semantic + procedural recall
  │
  ▼
QueryRouter                 Instructor typed: simple_lookup | rag | agentic
  │
  ▼
QueryRewriter               LLM, geçmiş turları kullanarak yazar
  │
  ▼
HybridRetriever             Qdrant dense + BM25 sparse → RRF füzyon
  │
  ▼
GraphRetriever              bilgi grafiği BFS komşu genişleme
  │
  ▼
LateInteractionReranker     ColBERT MaxSim token-window approximation
  │
  ▼
ContentFilter               PII redaction
  │
  ▼
LLM (Anthropic / OpenAI)   Anthropic prompt caching aktif; system prompt EPHEMERAl
  │
  ▼
OutputFilter                grounding overlap + refusal detection
  │
  ▼
SemanticCache.put           yanıtı önbelleğe yaz
  │
  ▼
MemoryManager.after_query   episodic özetle + procedural kaydet (kalite ≥ 0.75)
  │
  ▼
CostTracker + Prometheus    token sayaçları, latency histogram
  │
  ▼
Langfuse                    trace + generation kaydı
  │
  ▼
İstemciye QueryResponse
```

## Katman sorumlulukları

| Katman | Paket | Sorumluluk |
|---|---|---|
| API | `app/` | Routing, DI, hata yönetimi, auth, rate limit |
| Retrieval | `components/` | Hibrit arama, GraphRAG, reranking |
| İş mantığı | `services/` | RAG pipeline, LLM abstraction, cache, memory, MCP |
| Prompt | `prompts/` | Versiyonlu şablonlar, DSPy modülleri |
| Ajan | `agents/` | Doküman değerlendirme, sorgu ayrıştırma, araçlar, trajectory |
| Güvenlik | `security/` | Üç katmanlı guard zinciri |
| Değerlendirme | `evaluation/` | RAGAS, LLM-as-judge, metrikler, red-team |
| Gözlemlenebilirlik | `observability/` | OTel, Langfuse, Prometheus, maliyet |

## Bağımlılık yönü

```
app/ → services/ → components/
app/ → security/
app/ → observability/
services/ → prompts/
agents/ → services/
evaluation/ → services/ (sadece değerlendirme zamanı)
```

Döngüsel bağımlılık yasak. `app/` hiçbir zaman `evaluation/`'ı import etmez.

## Veri depolama

| Depo | Kullanım |
|---|---|
| Qdrant | Doküman vektörleri (dense retrieval) |
| Redis | Semantic cache, conversation, episodic/semantic/procedural memory, knowledge graph |
| Dosya sistemi | `evaluation/eval_results/`, `prompts/optimized/` |

## Ölçeklenebilirlik notları

- API pod'ları durumsuz; Redis ve Qdrant dışarıda tutulur
- Semantic cache Redis Cluster'a geçişe hazır
- Knowledge graph büyük veri setleri için Neo4j'ye taşınabilir
- Qdrant sharding yerleşik desteklidir
- LLM çağrıları tenacity ile yeniden denenir; upstream devre dışıysa graceful degradation

## Güvenlik sınırları

```
İstemci (güvenilmez)
  │  TLS
  ▼
API gateway / load balancer
  │
  ▼
FastAPI (InputGuard → ContentFilter → OutputFilter)
  │  iç ağ
  ▼
Qdrant / Redis / LLM API'leri (güvenilir bölge)
```
