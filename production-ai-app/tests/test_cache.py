import pytest

from services.semantic_cache import _cosine


def test_cosine_orthogonal_is_zero():
    assert _cosine([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_cosine_identical_is_one():
    assert _cosine([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_cosine_zero_vector_returns_zero():
    assert _cosine([0.0, 0.0], [1.0, 1.0]) == 0.0
