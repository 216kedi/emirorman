import pytest

from evaluation.metrics import (
    RetrievalMetrics,
    compute_all,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_recall_perfect():
    assert recall_at_k(["a", "b", "c"], ["a", "b"], k=5) == 1.0


def test_recall_partial():
    assert recall_at_k(["a", "x", "y"], ["a", "b"], k=5) == 0.5


def test_recall_k_cutoff():
    assert recall_at_k(["x", "a"], ["a"], k=1) == 0.0


def test_precision_at_k():
    assert precision_at_k(["a", "b", "x"], ["a", "b"], k=3) == pytest.approx(2 / 3)


def test_mrr_first_hit():
    assert mean_reciprocal_rank(["a", "b"], ["a"]) == 1.0


def test_mrr_second_hit():
    assert mean_reciprocal_rank(["x", "a"], ["a"]) == pytest.approx(0.5)


def test_mrr_no_hit():
    assert mean_reciprocal_rank(["x", "y"], ["a"]) == 0.0


def test_ndcg_perfect():
    assert ndcg_at_k(["a", "b"], ["a", "b"], k=2) == pytest.approx(1.0)


def test_ndcg_empty_relevant():
    assert ndcg_at_k(["a"], [], k=5) == 0.0


def test_compute_all_returns_dataclass():
    result = compute_all(["a", "b", "c"], ["a", "c"], k=3)
    assert isinstance(result, RetrievalMetrics)
    assert result.k == 3
    assert 0.0 <= result.ndcg_at_k <= 1.0
