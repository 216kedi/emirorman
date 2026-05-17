"""Retrieval quality metrics: Recall@k, Precision@k, MRR, nDCG."""
import math
from dataclasses import dataclass


@dataclass
class RetrievalMetrics:
    recall_at_k: float
    precision_at_k: float
    mrr: float
    ndcg_at_k: float
    k: int


def recall_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    if not relevant:
        return 0.0
    top = set(retrieved[:k])
    return len(top & set(relevant)) / len(relevant)


def precision_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    if k == 0:
        return 0.0
    top = retrieved[:k]
    rel_set = set(relevant)
    return sum(1 for d in top if d in rel_set) / k


def mean_reciprocal_rank(retrieved: list[str], relevant: list[str]) -> float:
    rel_set = set(relevant)
    for rank, doc_id in enumerate(retrieved, start=1):
        if doc_id in rel_set:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    rel_set = set(relevant)

    def dcg(docs: list[str]) -> float:
        return sum(
            (1.0 if doc in rel_set else 0.0) / math.log2(i + 2)
            for i, doc in enumerate(docs[:k])
        )

    ideal = sorted([1 if d in rel_set else 0 for d in retrieved], reverse=True)
    ideal_docs = [str(i) for i, v in enumerate(ideal) if v][:k]
    ideal_dcg = dcg(ideal_docs + [""] * k)
    actual_dcg = dcg(retrieved)
    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


def compute_all(retrieved: list[str], relevant: list[str], k: int = 5) -> RetrievalMetrics:
    return RetrievalMetrics(
        recall_at_k=recall_at_k(retrieved, relevant, k),
        precision_at_k=precision_at_k(retrieved, relevant, k),
        mrr=mean_reciprocal_rank(retrieved, relevant),
        ndcg_at_k=ndcg_at_k(retrieved, relevant, k),
        k=k,
    )
