from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from app.logging import get_logger
from services.embeddings import EmbeddingService
from services.vector_store import QdrantStore, VectorHit

log = get_logger(__name__)


@dataclass
class RetrievedChunk:
    doc_id: str
    text: str
    score: float
    source: str
    dense_score: float = 0.0
    sparse_score: float = 0.0


def _reciprocal_rank_fusion(
    rankings: list[list[str]], k: int = 60
) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return scores


class HybridRetriever:
    def __init__(
        self,
        store: QdrantStore,
        embedder: EmbeddingService,
        bm25_corpus: list[VectorHit] | None = None,
        alpha: float = 0.6,
    ) -> None:
        self.store = store
        self.embedder = embedder
        self.alpha = alpha
        self._bm25_corpus = bm25_corpus or []
        self._bm25_index = self._build_bm25_index(self._bm25_corpus)

    def _build_bm25_index(self, corpus: list[VectorHit]) -> BM25Okapi | None:
        if not corpus:
            return None
        tokenized = [hit.text.lower().split() for hit in corpus]
        return BM25Okapi(tokenized)

    def update_bm25_corpus(self, corpus: list[VectorHit]) -> None:
        self._bm25_corpus = corpus
        self._bm25_index = self._build_bm25_index(corpus)

    async def retrieve(self, query: str, top_k: int = 20) -> list[RetrievedChunk]:
        vector = await self.embedder.embed_one(query)
        dense_hits = await self.store.search(vector, top_k=top_k)

        sparse_hits: list[tuple[VectorHit, float]] = []
        if self._bm25_index is not None and self._bm25_corpus:
            scores = self._bm25_index.get_scores(query.lower().split())
            ranked = sorted(
                zip(self._bm25_corpus, scores, strict=True),
                key=lambda x: x[1],
                reverse=True,
            )[:top_k]
            sparse_hits = [(hit, float(score)) for hit, score in ranked]

        dense_rank = [h.doc_id for h in dense_hits]
        sparse_rank = [h.doc_id for h, _ in sparse_hits]
        fused = _reciprocal_rank_fusion([dense_rank, sparse_rank])

        by_id: dict[str, VectorHit] = {h.doc_id: h for h in dense_hits}
        for h, _ in sparse_hits:
            by_id.setdefault(h.doc_id, h)

        sparse_score_map = {h.doc_id: s for h, s in sparse_hits}
        dense_score_map = {h.doc_id: h.score for h in dense_hits}

        results: list[RetrievedChunk] = []
        for doc_id, fused_score in sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]:
            hit = by_id[doc_id]
            results.append(
                RetrievedChunk(
                    doc_id=doc_id,
                    text=hit.text,
                    score=fused_score,
                    source=hit.source,
                    dense_score=dense_score_map.get(doc_id, 0.0),
                    sparse_score=sparse_score_map.get(doc_id, 0.0),
                )
            )

        log.info("hybrid_retrieve", query_len=len(query), dense=len(dense_hits), sparse=len(sparse_hits), fused=len(results))
        return results
