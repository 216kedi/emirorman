"""Online monitor: sample live traffic, judge sampled answers, alert on regressions."""
from __future__ import annotations

import random
from dataclasses import dataclass

from app.logging import get_logger
from evaluation.llm_judge import LLMJudge
from observability.langfuse_client import score as langfuse_score
from observability.metrics import QUERY_TOTAL

log = get_logger(__name__)


@dataclass
class OnlineSample:
    trace_id: str
    query: str
    context: str
    answer: str
    reference: str | None = None


class OnlineMonitor:
    def __init__(
        self,
        judge: LLMJudge | None = None,
        sample_rate: float = 0.05,
        alert_threshold: float = 0.6,
    ) -> None:
        self.judge = judge or LLMJudge()
        self.sample_rate = sample_rate
        self.alert_threshold = alert_threshold

    def should_sample(self) -> bool:
        return random.random() < self.sample_rate

    async def evaluate(self, sample: OnlineSample) -> dict:
        result = await self.judge.judge(
            query=sample.query,
            context=sample.context,
            answer=sample.answer,
            reference=sample.reference,
        )

        langfuse_score(trace_id=sample.trace_id, name="faithfulness", value=result.faithfulness)
        langfuse_score(trace_id=sample.trace_id, name="relevance", value=result.relevance)
        langfuse_score(trace_id=sample.trace_id, name="composite", value=result.composite)

        if result.composite < self.alert_threshold:
            log.warning(
                "online_quality_alert",
                trace_id=sample.trace_id,
                composite=result.composite,
                faithfulness=result.faithfulness,
                relevance=result.relevance,
            )

        return {
            "trace_id": sample.trace_id,
            "faithfulness": result.faithfulness,
            "relevance": result.relevance,
            "composite": result.composite,
        }
