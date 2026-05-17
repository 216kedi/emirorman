from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.errors import UpstreamError
from app.logging import get_logger
from services.llm.base import (
    CompletionRequest,
    CompletionResponse,
    CompletionUsage,
)

log = get_logger(__name__)


class AnthropicLLM:
    def __init__(self, api_key: str, default_model: str) -> None:
        self.client = AsyncAnthropic(api_key=api_key)
        self.default_model = default_model

    def _build_payload(self, request: CompletionRequest) -> dict:
        system_blocks: list[dict] = []
        messages: list[dict] = []
        for m in request.messages:
            block = {"type": "text", "text": m.content}
            if m.cache_control == "ephemeral":
                block["cache_control"] = {"type": "ephemeral"}
            if m.role == "system":
                system_blocks.append(block)
            else:
                messages.append({"role": m.role, "content": [block]})

        payload: dict = {
            "model": request.model or self.default_model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": messages,
        }
        if system_blocks:
            payload["system"] = system_blocks
        if request.stop_sequences:
            payload["stop_sequences"] = request.stop_sequences
        return payload

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        payload = self._build_payload(request)
        try:
            resp = await self.client.messages.create(**payload)
        except Exception as e:
            raise UpstreamError(f"Anthropic completion failed: {e}") from e

        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        usage = CompletionUsage(
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            cache_read_tokens=getattr(resp.usage, "cache_read_input_tokens", 0) or 0,
            cache_write_tokens=getattr(resp.usage, "cache_creation_input_tokens", 0) or 0,
        )
        log.info(
            "anthropic_completion",
            model=resp.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_read=usage.cache_read_tokens,
            cache_write=usage.cache_write_tokens,
        )
        return CompletionResponse(
            content=text,
            model=resp.model,
            usage=usage,
            stop_reason=resp.stop_reason,
        )

    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        payload = self._build_payload(request)
        try:
            async with self.client.messages.stream(**payload) as stream:
                async for chunk in stream.text_stream:
                    yield chunk
        except Exception as e:
            raise UpstreamError(f"Anthropic stream failed: {e}") from e
