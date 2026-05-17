from prometheus_client import Counter, Histogram, Gauge

QUERY_TOTAL = Counter(
    "rag_queries_total",
    "Total RAG queries",
    ["route", "cached", "environment"],
)

QUERY_LATENCY = Histogram(
    "rag_query_duration_seconds",
    "RAG query end-to-end latency",
    ["route"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

LLM_TOKENS = Counter(
    "llm_tokens_total",
    "LLM tokens consumed",
    ["type", "provider"],
)

LLM_CACHE_TOKENS = Counter(
    "llm_cache_tokens_total",
    "Anthropic prompt cache read/write tokens",
    ["direction"],
)

RETRIEVAL_LATENCY = Histogram(
    "retrieval_duration_seconds",
    "Hybrid retrieval latency",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0],
)

SEMANTIC_CACHE_HITS = Counter(
    "semantic_cache_hits_total",
    "Semantic cache hits",
)

GUARDRAIL_BLOCKS = Counter(
    "guardrail_blocks_total",
    "Requests blocked by guardrails",
    ["layer"],
)

ACTIVE_REQUESTS = Gauge(
    "active_requests",
    "Currently processing requests",
)
