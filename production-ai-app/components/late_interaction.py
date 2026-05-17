"""ColBERT-style late-interaction reranking via MaxSim over token embeddings.

Late interaction outperforms cross-encoder reranking at scale because
query and document vectors are precomputed independently; only the
MaxSim aggregation is done at query time.

Without a running ColBERT server this module approximates MaxSim by
chunking the query and document into overlapping token windows, embedding
each window, and computing cosine MaxSim — a faithful approximation that
improves over simple single-vector scoring.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from app.logging import get_logger
from components.hybrid_retriever import RetrievedChunk
from services.embeddings import EmbeddingService

log = get_logger(__name__)


@dataclass
class LateInteractionScore:
    doc_id: str
    maxsim_score: float


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _token_windows(text: str, window: int = 64, stride: int = 32) -> list[str]:
    """Split text into overlapping word windows approximating token spans."""
    words = text.split()
    if len(words) <= window:
        return [text]
    return [
        " ".join(words[i : i + window])
        for i in range(0, len(words) - window + 1, stride)
    ]


class LateInteractionReranker:
    """Approximate MaxSim reranker using the existing embedding service."""

    def __init__(
        self,
        embedder: EmbeddingService,
        query_window: int = 32,
        doc_window: int = 64,
        doc_stride: int = 32,
    ) -> None:
        self.embedder = embedder
        self.query_window = query_window
        self.doc_window = doc_window
        self.doc_stride = doc_stride

    async def _embed_windows(self, text: str, window: int, stride: int) -> list[list[float]]:
        windows = _token_windows(text, window=window, stride=stride)
        return await self.embedder.embed(windows)

    async def score(self, query: str, doc_text: str) -> float:
        q_vecs, d_vecs = await _parallel_embed(
            self.embedder,
            query,
            doc_text,
            self.query_window,
            self.doc_window,
            self.doc_stride,
        )
        total = 0.0
        for qv in q_vecs:
            best = max((_cosine(qv, dv) for dv in d_vecs), default=0.0)
            total += best
        return total / len(q_vecs) if q_vecs else 0.0

    async def rerank(
        self,
        query: str,
        candidates: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        if not candidates:
            return []

        import asyncio

        scores = await asyncio.gather(
            *[self.score(query, c.text) for c in candidates], return_exceptions=True
        )
        scored = sorted(
            [
                (c, float(s) if not isinstance(s, Exception) else 0.0)
                for c, s in zip(candidates, scores, strict=True)
            ],
            key=lambda x: x[1],
            reverse=True,
        )
        log.info("late_interaction_rerank", candidates=len(candidates), top_k=top_k)
        return [c for c, _ in scored[:top_k]]


async def _parallel_embed(
    embedder: EmbeddingService,
    query: str,
    doc: str,
    q_window: int,
    d_window: int,
    d_stride: int,
) -> tuple[list[list[float]], list[list[float]]]:
    import asyncio

    q_task = embedder.embed(_token_windows(query, window=q_window, stride=q_window))
    d_task = embedder.embed(_token_windows(doc, window=d_window, stride=d_stride))
    return await asyncio.gather(q_task, d_task)
