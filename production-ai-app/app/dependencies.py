from functools import lru_cache

from components.hybrid_retriever import HybridRetriever
from components.reranker import LLMReranker
from security.content_filter import ContentFilter
from security.input_guard import InputGuard
from security.output_filter import OutputFilter
from services.conversation import ConversationStore
from services.embeddings import EmbeddingService
from services.llm import build_default_client
from services.query_rewriter import QueryRewriter
from services.query_router import QueryRouter
from services.rag_pipeline import RAGDependencies, RAGPipeline
from services.semantic_cache import SemanticCache
from services.vector_store import QdrantStore


@lru_cache
def _embedder() -> EmbeddingService:
    return EmbeddingService()


@lru_cache
def _vector_store() -> QdrantStore:
    return QdrantStore()


@lru_cache
def _llm():
    return build_default_client()


@lru_cache
def _conversation_store() -> ConversationStore:
    return ConversationStore()


@lru_cache
def _cache() -> SemanticCache:
    return SemanticCache(embedder=_embedder())


@lru_cache
def get_pipeline() -> RAGPipeline:
    llm = _llm()
    deps = RAGDependencies(
        llm=llm,
        retriever=HybridRetriever(store=_vector_store(), embedder=_embedder()),
        reranker=LLMReranker(llm=llm),
        cache=_cache(),
        conversations=_conversation_store(),
        rewriter=QueryRewriter(llm=llm),
        router=QueryRouter(),
        input_guard=InputGuard(),
        content_filter=ContentFilter(),
        output_guard=OutputFilter(),
    )
    return RAGPipeline(deps)


async def shutdown() -> None:
    await _cache().aclose()
    await _conversation_store().aclose()
    await _vector_store().aclose()
