from dataclasses import dataclass

from app.logging import get_logger
from observability.metrics import LLM_CACHE_TOKENS, LLM_TOKENS

log = get_logger(__name__)

_PRICE_PER_1K: dict[str, dict[str, float]] = {
    "claude-opus-4-7": {"input": 0.015, "output": 0.075, "cache_read": 0.0015, "cache_write": 0.01875},
    "claude-sonnet-4-6": {"input": 0.003, "output": 0.015, "cache_read": 0.0003, "cache_write": 0.00375},
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
}


@dataclass
class CostEntry:
    trace_id: str
    component: str
    model: str
    provider: str
    tokens_in: int
    tokens_out: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def usd_cost(self) -> float:
        pricing = _PRICE_PER_1K.get(self.model, {"input": 0.0, "output": 0.0})
        return (
            self.tokens_in * pricing.get("input", 0.0) / 1000
            + self.tokens_out * pricing.get("output", 0.0) / 1000
            + self.cache_read_tokens * pricing.get("cache_read", 0.0) / 1000
            + self.cache_write_tokens * pricing.get("cache_write", 0.0) / 1000
        )


class CostTracker:
    def record(self, entry: CostEntry) -> None:
        LLM_TOKENS.labels(type="input", provider=entry.provider).inc(entry.tokens_in)
        LLM_TOKENS.labels(type="output", provider=entry.provider).inc(entry.tokens_out)
        if entry.cache_read_tokens:
            LLM_CACHE_TOKENS.labels(direction="read").inc(entry.cache_read_tokens)
        if entry.cache_write_tokens:
            LLM_CACHE_TOKENS.labels(direction="write").inc(entry.cache_write_tokens)
        log.info(
            "cost_recorded",
            trace_id=entry.trace_id,
            model=entry.model,
            usd=round(entry.usd_cost, 6),
            total_tokens=entry.tokens_in + entry.tokens_out,
        )
