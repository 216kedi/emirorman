from components.hybrid_retriever import _reciprocal_rank_fusion


def test_rrf_prefers_consensus_across_rankings():
    dense = ["a", "b", "c"]
    sparse = ["b", "a", "d"]
    fused = _reciprocal_rank_fusion([dense, sparse])
    ordered = sorted(fused.items(), key=lambda x: x[1], reverse=True)
    assert ordered[0][0] in {"a", "b"}
    assert ordered[1][0] in {"a", "b"}


def test_rrf_includes_singletons_with_lower_score():
    fused = _reciprocal_rank_fusion([["a", "b"], ["b", "c"]])
    assert "a" in fused and "b" in fused and "c" in fused
    assert fused["b"] > fused["a"]
    assert fused["b"] > fused["c"]
