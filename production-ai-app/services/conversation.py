from dataclasses import dataclass, field

import redis.asyncio as redis

from app.config import settings
from app.errors import CacheUnavailable
from app.logging import get_logger

log = get_logger(__name__)


@dataclass
class TurnMessage:
    role: str
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class Conversation:
    conversation_id: str
    messages: list[TurnMessage] = field(default_factory=list)

    def append(self, role: str, content: str) -> None:
        self.messages.append(TurnMessage(role=role, content=content))

    def last_n(self, n: int) -> list[TurnMessage]:
        return self.messages[-n:]


class ConversationStore:
    def __init__(self, url: str | None = None, ttl_seconds: int = 60 * 60 * 24 * 7) -> None:
        self.redis = redis.from_url(url or settings.redis_url, decode_responses=True)
        self.ttl = ttl_seconds

    @staticmethod
    def _key(conversation_id: str) -> str:
        return f"conversation:{conversation_id}"

    async def get(self, conversation_id: str) -> Conversation:
        try:
            raw = await self.redis.lrange(self._key(conversation_id), 0, -1)
        except Exception as e:
            raise CacheUnavailable(f"Conversation read failed: {e}") from e
        messages: list[TurnMessage] = []
        for entry in raw:
            role, _, content = entry.partition("\x00")
            messages.append(TurnMessage(role=role, content=content))
        return Conversation(conversation_id=conversation_id, messages=messages)

    async def append(self, conversation_id: str, role: str, content: str) -> None:
        encoded = f"{role}\x00{content}"
        key = self._key(conversation_id)
        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                await pipe.rpush(key, encoded)
                await pipe.expire(key, self.ttl)
                await pipe.execute()
        except Exception as e:
            raise CacheUnavailable(f"Conversation write failed: {e}") from e

    async def aclose(self) -> None:
        await self.redis.aclose()
