"""Semantic memory: extracted user facts stored as searchable embeddings.

Enables personalisation: "the user prefers concise answers", "user works
in healthcare", "user's timezone is UTC+3". Facts are embedded and
retrieved by cosine similarity at query time so only relevant facts are
injected into context.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

import redis.asyncio as aioredis

from app.config import settings
from app.logging import get_logger
from services.embeddings import EmbeddingService

log = get_logger(__name__)

_FACTS_KEY = "memory:semantic:{user_id}:facts"
_VEC_KEY = "memory:semantic:{user_id}:vecs"


@dataclass
class Fact:
    text: str
    confidence: float = 1.0
    source: str = "inferred"


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class SemanticMemory:
    def __init__(self, embedder: EmbeddingService, url: str | None = None, ttl: int = 60 * 60 * 24 * 90) -> None:
        self.embedder = embedder
        self.redis = aioredis.from_url(url or settings.redis_url, decode_responses=True)
        self.ttl = ttl

    @staticmethod
    def _digest(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    async def store(self, user_id: str, fact: Fact) -> None:
        digest = self._digest(fact.text)
        vec = await self.embedder.embed_one(fact.text)
        fkey = _FACTS_KEY.format(user_id=user_id)
        vkey = _VEC_KEY.format(user_id=user_id)
        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.hset(fkey, digest, json.dumps({"text": fact.text, "confidence": fact.confidence, "source": fact.source}))
            await pipe.hset(vkey, digest, json.dumps(vec))
            await pipe.expire(fkey, self.ttl)
            await pipe.expire(vkey, self.ttl)
            await pipe.execute()
        log.info("semantic_memory_stored", user_id=user_id, fact_digest=digest)

    async def recall(self, user_id: str, query: str, top_k: int = 5, threshold: float = 0.7) -> list[Fact]:
        fkey = _FACTS_KEY.format(user_id=user_id)
        vkey = _VEC_KEY.format(user_id=user_id)
        facts_raw, vecs_raw = await self.redis.hgetall(fkey), await self.redis.hgetall(vkey)
        if not facts_raw:
            return []

        q_vec = await self.embedder.embed_one(query)
        scored: list[tuple[float, Fact]] = []
        for digest, vec_json in vecs_raw.items():
            if digest not in facts_raw:
                continue
            try:
                vec = json.loads(vec_json)
                fact_data = json.loads(facts_raw[digest])
            except Exception:
                continue
            score = _cosine(q_vec, vec)
            if score >= threshold:
                scored.append((score, Fact(**fact_data)))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:top_k]]

    async def aclose(self) -> None:
        await self.redis.aclose()
