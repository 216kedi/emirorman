from app.logging import get_logger
from components.hybrid_retriever import RetrievedChunk
from services.llm.base import LLMClient, CompletionRequest, Message

log = get_logger(__name__)


_RERANK_SYSTEM = (
    "You are a strict relevance scorer. For each numbered passage, output a single "
    "integer 0-10 (10 = perfect, 0 = irrelevant) on its own line, in order. "
    "No prose, no explanations."
)


class LLMReranker:
    def __init__(self, llm: LLMClient, model: str | None = None) -> None:
        self.llm = llm
        self.model = model

    async def rerank(
        self,
        query: str,
        candidates: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        if not candidates:
            return []
        if len(candidates) <= top_k:
            return candidates

        passages = "\n\n".join(
            f"[{i + 1}] {c.text[:800]}" for i, c in enumerate(candidates)
        )
        user = f"Query: {query}\n\nPassages:\n{passages}\n\nScores:"

        request = CompletionRequest(
            messages=[
                Message(role="system", content=_RERANK_SYSTEM),
                Message(role="user", content=user),
            ],
            model=self.model or "",
            max_tokens=256,
            temperature=0.0,
        )
        resp = await self.llm.complete(request)

        scores: list[float] = []
        for line in resp.content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                scores.append(float(line.split()[0]))
            except (ValueError, IndexError):
                continue

        if len(scores) < len(candidates):
            log.warning("rerank_parse_short", expected=len(candidates), got=len(scores))
            scores.extend([0.0] * (len(candidates) - len(scores)))

        scored = sorted(
            zip(candidates, scores[: len(candidates)], strict=True),
            key=lambda x: x[1],
            reverse=True,
        )
        return [c for c, _ in scored[:top_k]]
