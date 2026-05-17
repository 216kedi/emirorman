"""Episodic memory: time-ordered conversation episodes with recency decay.

Different from ConversationStore (raw turns) — episodic memory stores
summarised episodes so long sessions don't inflate context length.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass

import redis.asyncio as aioredis

from app.config import settings
from app.logging import get_logger

log = get_logger(__name__)

_EP_KEY = "memory:episodic:{user_id}"


@dataclass
class Episode:
    summary: str
    timestamp: float
    relevance_score: float = 1.0

    def to_dict(self) -> dict:
        return {"summary": self.summary, "timestamp": self.timestamp, "relevance": self.relevance_score}

    @classmethod
    def from_dict(cls, d: dict) -> "Episode":
        return cls(summary=d["summary"], timestamp=d["timestamp"], relevance_score=d.get("relevance", 1.0))


class EpisodicMemory:
    def __init__(self, url: str | None = None, max_episodes: int = 50, ttl: int = 60 * 60 * 24 * 30) -> None:
        self.redis = aioredis.from_url(url or settings.redis_url, decode_responses=True)
        self.max_episodes = max_episodes
        self.ttl = ttl

    async def store(self, user_id: str, summary: str) -> None:
        episode = Episode(summary=summary, timestamp=time.time())
        key = _EP_KEY.format(user_id=user_id)
        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.rpush(key, json.dumps(episode.to_dict()))
            await pipe.ltrim(key, -self.max_episodes, -1)
            await pipe.expire(key, self.ttl)
            await pipe.execute()

    async def recall(self, user_id: str, n: int = 10) -> list[Episode]:
        key = _EP_KEY.format(user_id=user_id)
        raw = await self.redis.lrange(key, -n, -1)
        episodes = []
        for r in raw:
            try:
                episodes.append(Episode.from_dict(json.loads(r)))
            except Exception:
                continue
        return sorted(episodes, key=lambda e: e.timestamp, reverse=True)

    async def aclose(self) -> None:
        await self.redis.aclose()
