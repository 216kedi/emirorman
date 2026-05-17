from app.logging import get_logger
from services.llm.base import CompletionRequest, LLMClient, Message

log = get_logger(__name__)

_SYSTEM = (
    "You rewrite a user query for retrieval over a knowledge base. "
    "Preserve intent, expand ambiguous references using prior turns, "
    "remove conversational filler. Output ONLY the rewritten query."
)


class QueryRewriter:
    def __init__(self, llm: LLMClient, model: str | None = None) -> None:
        self.llm = llm
        self.model = model

    async def rewrite(self, query: str, history: list[str] | None = None) -> str:
        history_block = ""
        if history:
            history_block = "Recent turns:\n" + "\n".join(f"- {h}" for h in history[-4:]) + "\n\n"

        request = CompletionRequest(
            messages=[
                Message(role="system", content=_SYSTEM),
                Message(role="user", content=f"{history_block}Original query: {query}\nRewritten:"),
            ],
            model=self.model or "",
            max_tokens=200,
            temperature=0.0,
        )
        resp = await self.llm.complete(request)
        rewritten = resp.content.strip()
        log.info("query_rewritten", original_len=len(query), rewritten_len=len(rewritten))
        return rewritten or query
