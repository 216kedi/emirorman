from collections.abc import AsyncIterator
from typing import Literal, Protocol

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    cache_control: Literal["ephemeral"] | None = None


class CompletionRequest(BaseModel):
    messages: list[Message]
    model: str
    max_tokens: int = 1024
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    stop_sequences: list[str] = Field(default_factory=list)


class CompletionUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


class CompletionResponse(BaseModel):
    content: str
    model: str
    usage: CompletionUsage
    stop_reason: str | None = None


class LLMClient(Protocol):
    async def complete(self, request: CompletionRequest) -> CompletionResponse: ...

    def stream(self, request: CompletionRequest) -> AsyncIterator[str]: ...
