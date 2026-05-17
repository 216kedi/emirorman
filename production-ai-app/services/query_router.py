from enum import Enum

import instructor
from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

from app.config import settings
from app.logging import get_logger

log = get_logger(__name__)


class Route(str, Enum):
    SIMPLE_LOOKUP = "simple_lookup"
    RAG = "rag"
    AGENTIC = "agentic"


class RoutingDecision(BaseModel):
    route: Route
    reason: str = Field(..., max_length=240)
    needs_web: bool = False


_SYSTEM = (
    "Classify a user query into one of: simple_lookup, rag, agentic. "
    "simple_lookup = greeting/trivial, rag = needs internal knowledge base, "
    "agentic = needs multi-step tool use or external sources. Be concise."
)


class QueryRouter:
    def __init__(self, model: str | None = None) -> None:
        anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.client = instructor.from_anthropic(anthropic_client)
        self.model = model or settings.default_llm_model

    async def route(self, query: str) -> RoutingDecision:
        decision = await self.client.messages.create(
            model=self.model,
            max_tokens=200,
            messages=[
                {"role": "user", "content": f"Query: {query}"},
            ],
            system=_SYSTEM,
            response_model=RoutingDecision,
        )
        log.info("query_routed", route=decision.route.value, needs_web=decision.needs_web)
        return decision
