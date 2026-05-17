"""Procedural memory: successful query→strategy patterns.

When a complex query is answered well (high judge score), we store the
routing decision + rewrite strategy. On future similar queries this
memory short-circuits expensive routing/rewriting by suggesting a
proven approach.

Stored as: query_embedding → {route, rewrite_hint, success_count}.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass

import redis.asyncio as aioredis

from app.config import settings
from app.logging import get_logger
from services.embeddings import EmbeddingService

log = get_logger(__name__)

_PROC_KEY = "memory:procedural:patterns"
_VEC_KEY = "memory:procedural:vecs"


@dataclass
class Procedure:
    query_digest: str
    route: str
    rewrite_hint: str
    success_count: int = 1
    avg_score: float = 1.0


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class ProceduralMemory:
    def __init__(
        self,
        embedder: EmbeddingService,
        url: str | None = None,
        similarity_threshold: float = 0.92,
        ttl: int = 60 * 60 * 24 * 180,
    ) -> None:
        self.embedder = embedder
        self.redis = aioredis.from_url(url or settings.redis_url, decode_responses=True)
        self.threshold = similarity_threshold
        self.ttl = ttl

    async def record(self, query: str, route: str, rewrite_hint: str, score: float) -> None:
        import hashlib

        digest = hashlib.sha256(query.encode()).hexdigest()[:16]
        vec = await self.embedder.embed_one(query)
        existing_raw = await self.redis.hget(_PROC_KEY, digest)
        if existing_raw:
            proc = Procedure(**json.loads(existing_raw))
            proc.success_count += 1
            proc.avg_score = (proc.avg_score * (proc.success_count - 1) + score) / proc.success_count
        else:
            proc = Procedure(query_digest=digest, route=route, rewrite_hint=rewrite_hint, avg_score=score)

        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.hset(_PROC_KEY, digest, json.dumps(proc.__dict__))
            await pipe.hset(_VEC_KEY, digest, json.dumps(vec))
            await pipe.expire(_PROC_KEY, self.ttl)
            await pipe.expire(_VEC_KEY, self.ttl)
            await pipe.execute()

    async def lookup(self, query: str) -> Procedure | None:
        vecs_raw = await self.redis.hgetall(_VEC_KEY)
        if not vecs_raw:
            return None

        q_vec = await self.embedder.embed_one(query)
        best_score = 0.0
        best_digest: str | None = None
        for digest, vec_json in vecs_raw.items():
            try:
                score = _cosine(q_vec, json.loads(vec_json))
            except Exception:
                continue
            if score > best_score:
                best_score, best_digest = score, digest

        if best_digest is None or best_score < self.threshold:
            return None

        raw = await self.redis.hget(_PROC_KEY, best_digest)
        if raw is None:
            return None
        log.info("procedural_memory_hit", score=best_score, digest=best_digest)
        return Procedure(**json.loads(raw))

    async def aclose(self) -> None:
        await self.redis.aclose()
