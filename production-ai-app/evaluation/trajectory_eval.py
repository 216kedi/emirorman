"""Agent trajectory evaluation.

Tek-tur Q&A'nın ötesi: çok adımlı ajan akışlarını değerlendirir.
Her adım (tool_call, retrieval, rewrite, answer) için:
  - Strateji doğruluğu (beklenen araç seti kullanıldı mı?)
  - Adım verimliliği (gereksiz adım var mı?)
  - Nihai sonuç kalitesi (LLM-as-judge)
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum

import instructor
from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

from app.config import settings
from app.logging import get_logger

log = get_logger(__name__)


class StepType(str, Enum):
    ROUTE = "route"
    REWRITE = "rewrite"
    RETRIEVE = "retrieve"
    RERANK = "rerank"
    GENERATE = "generate"
    TOOL_CALL = "tool_call"
    SAFETY_CHECK = "safety_check"


@dataclass
class TrajectoryStep:
    step_type: StepType
    input: str
    output: str
    latency_ms: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class Trajectory:
    trace_id: str
    query: str
    steps: list[TrajectoryStep]
    final_answer: str
    expected_answer: str | None = None

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def total_latency_ms(self) -> float:
        return sum(s.latency_ms for s in self.steps)

    def steps_of_type(self, step_type: StepType) -> list[TrajectoryStep]:
        return [s for s in self.steps if s.step_type == step_type]


class TrajectoryScore(BaseModel):
    strategy_score: float = Field(..., ge=0.0, le=1.0, description="Correct tools/steps used")
    efficiency_score: float = Field(..., ge=0.0, le=1.0, description="No unnecessary steps")
    answer_quality: float = Field(..., ge=0.0, le=1.0, description="Final answer quality")
    reasoning: str = Field(..., max_length=500)
    redundant_steps: list[str] = Field(default_factory=list)


_JUDGE_SYSTEM = (
    "You are an expert AI system evaluator. You evaluate multi-step agent trajectories. "
    "Score three dimensions (0-1): strategy (right tools chosen), efficiency (no wasted steps), "
    "answer quality (final answer is correct and grounded). "
    "List any redundant step types. Return structured JSON only."
)


@dataclass
class TrajectoryEvalResult:
    trace_id: str
    scores: TrajectoryScore
    step_count: int
    total_latency_ms: float

    @property
    def composite(self) -> float:
        return (self.scores.strategy_score + self.scores.efficiency_score + self.scores.answer_quality) / 3


class TrajectoryEvaluator:
    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.default_llm_model
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.client = instructor.from_anthropic(client)

    def _format_trajectory(self, traj: Trajectory) -> str:
        lines = [f"Query: {traj.query}", f"Steps ({traj.step_count}):"]
        for i, step in enumerate(traj.steps, 1):
            lines.append(f"  {i}. [{step.step_type.value}] in={step.input[:80]} → out={step.output[:80]}")
        lines.append(f"Final answer: {traj.final_answer[:300]}")
        if traj.expected_answer:
            lines.append(f"Expected: {traj.expected_answer[:300]}")
        return "\n".join(lines)

    async def evaluate(self, trajectory: Trajectory) -> TrajectoryEvalResult:
        formatted = self._format_trajectory(trajectory)
        scores: TrajectoryScore = await self.client.messages.create(
            model=self.model,
            max_tokens=512,
            system=_JUDGE_SYSTEM,
            messages=[{"role": "user", "content": formatted}],
            response_model=TrajectoryScore,
        )
        result = TrajectoryEvalResult(
            trace_id=trajectory.trace_id,
            scores=scores,
            step_count=trajectory.step_count,
            total_latency_ms=trajectory.total_latency_ms,
        )
        log.info(
            "trajectory_eval",
            trace_id=trajectory.trace_id,
            composite=result.composite,
            steps=trajectory.step_count,
        )
        return result

    async def evaluate_batch(self, trajectories: list[Trajectory]) -> list[TrajectoryEvalResult]:
        return list(await asyncio.gather(*[self.evaluate(t) for t in trajectories]))


def summarize(results: list[TrajectoryEvalResult]) -> dict:
    if not results:
        return {}
    n = len(results)
    return {
        "n": n,
        "avg_composite": round(sum(r.composite for r in results) / n, 3),
        "avg_strategy": round(sum(r.scores.strategy_score for r in results) / n, 3),
        "avg_efficiency": round(sum(r.scores.efficiency_score for r in results) / n, 3),
        "avg_answer_quality": round(sum(r.scores.answer_quality for r in results) / n, 3),
        "avg_steps": round(sum(r.step_count for r in results) / n, 1),
        "avg_latency_ms": round(sum(r.total_latency_ms for r in results) / n, 1),
    }
