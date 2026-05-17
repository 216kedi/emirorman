"""End-to-end RAG pipeline orchestration."""
from app.models import QueryRequest, QueryResponse


class RAGPipeline:
    def __init__(self, retriever, reranker, llm, cache, router, rewriter) -> None:
        self.retriever = retriever
        self.reranker = reranker
        self.llm = llm
        self.cache = cache
        self.router = router
        self.rewriter = rewriter

    def run(self, request: QueryRequest) -> QueryResponse:
        raise NotImplementedError
