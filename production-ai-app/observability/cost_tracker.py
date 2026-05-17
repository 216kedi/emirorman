"""Per-trace cost breakdown across LLM, embedding, and storage calls."""
from dataclasses import dataclass


@dataclass
class CostEntry:
    trace_id: str
    component: str
    tokens_in: int
    tokens_out: int
    usd_cost: float


class CostTracker:
    def record(self, entry: CostEntry) -> None:
        raise NotImplementedError

    def summary(self, trace_id: str) -> dict:
        raise NotImplementedError
