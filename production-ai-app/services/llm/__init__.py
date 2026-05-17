from app.config import settings
from services.llm.anthropic_client import AnthropicLLM
from services.llm.base import (
    CompletionRequest,
    CompletionResponse,
    CompletionUsage,
    LLMClient,
    Message,
)
from services.llm.openai_client import OpenAILLM


def build_default_client() -> LLMClient:
    if settings.default_llm_provider == "anthropic":
        return AnthropicLLM(
            api_key=settings.anthropic_api_key,
            default_model=settings.default_llm_model,
        )
    return OpenAILLM(
        api_key=settings.openai_api_key,
        default_model=settings.default_llm_model,
    )


__all__ = [
    "AnthropicLLM",
    "CompletionRequest",
    "CompletionResponse",
    "CompletionUsage",
    "LLMClient",
    "Message",
    "OpenAILLM",
    "build_default_client",
]
