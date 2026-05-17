"""LLM-as-judge pipeline: faithfulness, relevance, groundedness."""
import asyncio
from dataclasses import dataclass

import instructor
from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

from app.config import settings
from app.logging import get_logger

log = get_logger(__name__)


class FaithfulnessScore(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="0=hallucinated, 1=fully grounded")
    reasoning: str = Field(..., max_length=400)
    unsupported_claims: list[str] = Field(default_factory=list)


class RelevanceScore(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="0=unrelated, 1=perfectly answers query")
    reasoning: str = Field(..., max_length=400)


class AnswerCorrectnessScore(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., max_length=400)
    missing_points: list[str] = Field(default_factory=list)


@dataclass
class JudgeResult:
    faithfulness: float
    relevance: float
    correctness: float | None
    reasoning: dict[str, str]

    @property
    def composite(self) -> float:
        scores = [self.faithfulness, self.relevance]
        if self.correctness is not None:
            scores.append(self.correctness)
        return sum(scores) / len(scores)


_FAITHFULNESS_SYSTEM = (
    "You are a strict factual auditor. Given a context and an answer, "
    "score how faithfully the answer is grounded in the context (0-1). "
    "Flag any claims not supported by the context."
)

_RELEVANCE_SYSTEM = (
    "You are a strict relevance judge. Given a query and an answer, "
    "score how directly and completely the answer addresses the query (0-1)."
)

_CORRECTNESS_SYSTEM = (
    "You are a strict correctness evaluator. Given a query, a reference answer, "
    "and a generated answer, score how correct the generated answer is (0-1). "
    "List important points missing from the generated answer."
)


class LLMJudge:
    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.default_llm_model
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.client = instructor.from_anthropic(client)

    async def score_faithfulness(self, context: str, answer: str) -> FaithfulnessScore:
        return await self.client.messages.create(
            model=self.model,
            max_tokens=512,
            system=_FAITHFULNESS_SYSTEM,
            messages=[{"role": "user", "content": f"Context:\n{context}\n\nAnswer:\n{answer}"}],
            response_model=FaithfulnessScore,
        )

    async def score_relevance(self, query: str, answer: str) -> RelevanceScore:
        return await self.client.messages.create(
            model=self.model,
            max_tokens=512,
            system=_RELEVANCE_SYSTEM,
            messages=[{"role": "user", "content": f"Query: {query}\n\nAnswer:\n{answer}"}],
            response_model=RelevanceScore,
        )

    async def score_correctness(self, query: str, reference: str, answer: str) -> AnswerCorrectnessScore:
        return await self.client.messages.create(
            model=self.model,
            max_tokens=512,
            system=_CORRECTNESS_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"Query: {query}\n\nReference:\n{reference}\n\nGenerated:\n{answer}",
            }],
            response_model=AnswerCorrectnessScore,
        )

    async def judge(
        self,
        query: str,
        context: str,
        answer: str,
        reference: str | None = None,
    ) -> JudgeResult:
        tasks = [
            self.score_faithfulness(context, answer),
            self.score_relevance(query, answer),
        ]
        if reference:
            tasks.append(self.score_correctness(query, reference, answer))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        faith = results[0] if not isinstance(results[0], Exception) else None
        rel = results[1] if not isinstance(results[1], Exception) else None
        corr = results[2] if len(results) > 2 and not isinstance(results[2], Exception) else None

        return JudgeResult(
            faithfulness=faith.score if faith else 0.0,
            relevance=rel.score if rel else 0.0,
            correctness=corr.score if corr else None,
            reasoning={
                "faithfulness": faith.reasoning if faith else "error",
                "relevance": rel.reasoning if rel else "error",
                "correctness": corr.reasoning if corr else "",
            },
        )
