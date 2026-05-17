"""Cross-encoder reranker applied on top of hybrid retrieval candidates."""
from components.hybrid_retriever import RetrievedChunk


class Reranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-large") -> None:
        self.model_name = model_name

    def rerank(self, query: str, candidates: list[RetrievedChunk], top_k: int = 5) -> list[RetrievedChunk]:
        raise NotImplementedError
