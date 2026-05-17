from collections.abc import AsyncIterator

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.errors import UpstreamError
from app.logging import get_logger
from services.llm.base import (
    CompletionRequest,
    CompletionResponse,
    CompletionUsage,
)

log = get_logger(__name__)


class OpenAILLM:
    def __init__(self, api_key: str, default_model: str) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.default_model = default_model

    def _to_openai_messages(self, request: CompletionRequest) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in request.messages]

    @retry(reraise=True, stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        try:
            resp = await self.client.chat.completions.create(
                model=request.model or self.default_model,
                messages=self._to_openai_messages(request),
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stop=request.stop_sequences or None,
            )
        except Exception as e:
            raise UpstreamError(f"OpenAI completion failed: {e}") from e

        choice = resp.choices[0]
        usage = CompletionUsage(
            input_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            output_tokens=resp.usage.completion_tokens if resp.usage else 0,
            cache_read_tokens=getattr(resp.usage, "prompt_tokens_cached", 0) or 0,
        )
        return CompletionResponse(
            content=choice.message.content or "",
            model=resp.model,
            usage=usage,
            stop_reason=choice.finish_reason,
        )

    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        try:
            stream = await self.client.chat.completions.create(
                model=request.model or self.default_model,
                messages=self._to_openai_messages(request),
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
        except Exception as e:
            raise UpstreamError(f"OpenAI stream failed: {e}") from e
