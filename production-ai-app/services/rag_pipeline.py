from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.errors import GuardrailBlocked
from app.logging import get_logger
from app.models import Citation, QueryRequest, QueryResponse, Usage
from components.hybrid_retriever import HybridRetriever, RetrievedChunk
from components.reranker import LLMReranker
from prompts.registry import get as get_prompt
from security.content_filter import ContentFilter
from security.input_guard import InputGuard
from security.output_filter import OutputFilter
from services.conversation import ConversationStore
from services.llm.base import CompletionRequest, LLMClient, Message
from services.query_rewriter import QueryRewriter
from services.query_router import QueryRouter, Route
from services.semantic_cache import SemanticCache

log = get_logger(__name__)


@dataclass
class RAGDependencies:
    llm: LLMClient
    retriever: HybridRetriever
    reranker: LLMReranker
    cache: SemanticCache
    conversations: ConversationStore
    rewriter: QueryRewriter
    router: QueryRouter
    input_guard: InputGuard
    content_filter: ContentFilter
    output_guard: OutputFilter


def _format_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(f"[{i + 1}] ({c.source}) {c.text}" for i, c in enumerate(chunks))


def _to_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    return [
        Citation(source=c.source or c.doc_id, score=c.score, snippet=c.text[:240])
        for c in chunks
    ]


class RAGPipeline:
    def __init__(self, deps: RAGDependencies) -> None:
        self.deps = deps

    async def _prepare(self, request: QueryRequest, trace_id: str) -> tuple[str, list[RetrievedChunk]]:
        guard = self.deps.input_guard.check(request.query)
        if not guard.allowed:
            raise GuardrailBlocked(guard.reason or "Input blocked by guardrail")

        history: list[str] = []
        if request.conversation_id:
            conv = await self.deps.conversations.get(request.conversation_id)
            history = [m.content for m in conv.last_n(6)]

        decision = await self.deps.router.route(request.query)
        log.info("router_decision", trace_id=trace_id, route=decision.route.value)

        rewritten = await self.deps.rewriter.rewrite(request.query, history=history)

        if decision.route == Route.SIMPLE_LOOKUP:
            return rewritten, []

        candidates = await self.deps.retriever.retrieve(rewritten, top_k=20)
        top = await self.deps.reranker.rerank(rewritten, candidates, top_k=5)
        top = [
            RetrievedChunk(
                doc_id=c.doc_id,
                text=self.deps.content_filter.filter(c.text),
                score=c.score,
                source=c.source,
                dense_score=c.dense_score,
                sparse_score=c.sparse_score,
            )
            for c in top
        ]
        return rewritten, top

    async def run(self, request: QueryRequest, trace_id: str) -> QueryResponse:
        cached = await self.deps.cache.get(request.query)
        if cached is not None:
            return QueryResponse(answer=cached, trace_id=trace_id, cached=True)

        rewritten, context = await self._prepare(request, trace_id)
        prompt = get_prompt("rag_answer", "v1")
        rendered = prompt.render(
            context=_format_context(context) if context else "(no context)",
            question=request.query,
        )

        completion = await self.deps.llm.complete(
            CompletionRequest(
                messages=[
                    Message(
                        role="system",
                        content="You are a careful, citation-grounded assistant.",
                        cache_control="ephemeral",
                    ),
                    Message(role="user", content=rendered),
                ],
                model="",
                max_tokens=1024,
            )
        )

        guard = self.deps.output_guard.check(completion.content, context=_format_context(context))
        if not guard.allowed:
            raise GuardrailBlocked(guard.reason or "Output blocked by guardrail")

        if request.conversation_id:
            await self.deps.conversations.append(request.conversation_id, "user", request.query)
            await self.deps.conversations.append(request.conversation_id, "assistant", completion.content)

        await self.deps.cache.put(request.query, completion.content)

        return QueryResponse(
            answer=completion.content,
            citations=_to_citations(context),
            trace_id=trace_id,
            usage=Usage(
                input_tokens=completion.usage.input_tokens,
                output_tokens=completion.usage.output_tokens,
                cache_read_tokens=completion.usage.cache_read_tokens,
                cache_write_tokens=completion.usage.cache_write_tokens,
            ),
        )

    async def stream(self, request: QueryRequest, trace_id: str) -> AsyncIterator[str]:
        rewritten, context = await self._prepare(request, trace_id)
        prompt = get_prompt("rag_answer", "v1")
        rendered = prompt.render(
            context=_format_context(context) if context else "(no context)",
            question=request.query,
        )
        chunks: list[str] = []
        async for token in self.deps.llm.stream(
            CompletionRequest(
                messages=[
                    Message(
                        role="system",
                        content="You are a careful, citation-grounded assistant.",
                        cache_control="ephemeral",
                    ),
                    Message(role="user", content=rendered),
                ],
                model="",
                max_tokens=1024,
            )
        ):
            chunks.append(token)
            yield token

        full = "".join(chunks)
        if request.conversation_id:
            await self.deps.conversations.append(request.conversation_id, "user", request.query)
            await self.deps.conversations.append(request.conversation_id, "assistant", full)
        await self.deps.cache.put(request.query, full)
