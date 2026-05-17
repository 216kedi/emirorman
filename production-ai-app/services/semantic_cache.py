import hashlib
import json
import math

import redis.asyncio as redis

from app.config import settings
from app.errors import CacheUnavailable
from app.logging import get_logger
from services.embeddings import EmbeddingService

log = get_logger(__name__)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class SemanticCache:
    def __init__(
        self,
        embedder: EmbeddingService,
        url: str | None = None,
        threshold: float | None = None,
        ttl_seconds: int = 60 * 60 * 24,
        index_key: str = "semantic_cache:index",
    ) -> None:
        self.embedder = embedder
        self.threshold = threshold if threshold is not None else settings.semantic_cache_threshold
        self.ttl = ttl_seconds
        self.index_key = index_key
        self.redis = redis.from_url(url or settings.redis_url, decode_responses=True)

    @staticmethod
    def _key(digest: str) -> str:
        return f"semantic_cache:entry:{digest}"

    async def get(self, query: str) -> str | None:
        try:
            entries = await self.redis.hgetall(self.index_key)
        except Exception as e:
            raise CacheUnavailable(f"Redis read failed: {e}") from e
        if not entries:
            return None

        query_vec = await self.embedder.embed_one(query)
        best_score = 0.0
        best_digest: str | None = None
        for digest, vec_json in entries.items():
            try:
                vec = json.loads(vec_json)
            except json.JSONDecodeError:
                continue
            score = _cosine(query_vec, vec)
            if score > best_score:
                best_score = score
                best_digest = digest

        if best_digest is None or best_score < self.threshold:
            return None

        answer = await self.redis.get(self._key(best_digest))
        if answer is None:
            await self.redis.hdel(self.index_key, best_digest)
            return None
        log.info("semantic_cache_hit", score=best_score)
        return answer

    async def put(self, query: str, answer: str) -> None:
        try:
            vec = await self.embedder.embed_one(query)
            digest = hashlib.sha256(query.encode("utf-8")).hexdigest()
            await self.redis.set(self._key(digest), answer, ex=self.ttl)
            await self.redis.hset(self.index_key, digest, json.dumps(vec))
        except Exception as e:
            raise CacheUnavailable(f"Redis write failed: {e}") from e

    async def aclose(self) -> None:
        await self.redis.aclose()
