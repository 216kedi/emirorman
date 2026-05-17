"""Hybrid retrieval: dense (vector) + sparse (BM25) fusion."""
from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    doc_id: str
    text: str
    score: float
    source: str


class HybridRetriever:
    def __init__(self, dense_client, sparse_client, alpha: float = 0.6) -> None:
        self.dense_client = dense_client
        self.sparse_client = sparse_client
        self.alpha = alpha

    def retrieve(self, query: str, top_k: int = 20) -> list[RetrievedChunk]:
        raise NotImplementedError
