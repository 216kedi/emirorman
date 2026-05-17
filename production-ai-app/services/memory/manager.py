"""Unified memory manager: single entry point for all memory tiers.

Usage pattern:
  memory = MemoryManager(embedder)
  await memory.before_query(user_id, query)   → injects context
  await memory.after_query(user_id, query, answer, route, score)  → stores
"""
from __future__ import annotations

from dataclasses import dataclass

from app.logging import get_logger
from services.embeddings import EmbeddingService
from services.memory.episodic import Episode, EpisodicMemory
from services.memory.procedural import Procedure, ProceduralMemory
from services.memory.semantic import Fact, SemanticMemory

log = get_logger(__name__)


@dataclass
class MemoryContext:
    recent_episodes: list[Episode]
    relevant_facts: list[Fact]
    suggested_procedure: Procedure | None

    def to_prompt_block(self) -> str:
        lines: list[str] = []
        if self.relevant_facts:
            lines.append("User facts: " + "; ".join(f.text for f in self.relevant_facts[:3]))
        if self.recent_episodes:
            lines.append("Recent sessions: " + " | ".join(e.summary for e in self.recent_episodes[:3]))
        if self.suggested_procedure:
            lines.append(f"Suggested route: {self.suggested_procedure.route} — {self.suggested_procedure.rewrite_hint}")
        return "\n".join(lines)

    @property
    def is_empty(self) -> bool:
        return not self.relevant_facts and not self.recent_episodes and not self.suggested_procedure


class MemoryManager:
    def __init__(
        self,
        embedder: EmbeddingService,
        url: str | None = None,
        quality_threshold: float = 0.75,
    ) -> None:
        self.episodic = EpisodicMemory(url=url)
        self.semantic = SemanticMemory(embedder=embedder, url=url)
        self.procedural = ProceduralMemory(embedder=embedder, url=url)
        self.quality_threshold = quality_threshold

    async def before_query(self, user_id: str, query: str) -> MemoryContext:
        import asyncio

        episodes, facts, procedure = await asyncio.gather(
            self.episodic.recall(user_id, n=5),
            self.semantic.recall(user_id, query, top_k=3),
            self.procedural.lookup(query),
            return_exceptions=True,
        )
        ctx = MemoryContext(
            recent_episodes=episodes if not isinstance(episodes, Exception) else [],
            relevant_facts=facts if not isinstance(facts, Exception) else [],
            suggested_procedure=procedure if not isinstance(procedure, Exception) else None,
        )
        if not ctx.is_empty:
            log.info(
                "memory_context_loaded",
                user_id=user_id,
                episodes=len(ctx.recent_episodes),
                facts=len(ctx.relevant_facts),
                procedure=ctx.suggested_procedure is not None,
            )
        return ctx

    async def after_query(
        self,
        user_id: str,
        query: str,
        answer: str,
        route: str,
        rewrite_hint: str,
        quality_score: float,
    ) -> None:
        import asyncio

        tasks = []
        if quality_score >= self.quality_threshold:
            tasks.append(
                self.episodic.store(user_id, summary=f"Q: {query[:120]} A: {answer[:120]}")
            )
            tasks.append(
                self.procedural.record(query, route=route, rewrite_hint=rewrite_hint, score=quality_score)
            )
        await asyncio.gather(*tasks, return_exceptions=True)

    async def store_fact(self, user_id: str, fact: Fact) -> None:
        await self.semantic.store(user_id, fact)

    async def aclose(self) -> None:
        import asyncio

        await asyncio.gather(
            self.episodic.aclose(),
            self.semantic.aclose(),
            self.procedural.aclose(),
            return_exceptions=True,
        )
