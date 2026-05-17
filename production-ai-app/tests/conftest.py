import pytest


@pytest.fixture
def sample_chunks():
    from components.hybrid_retriever import RetrievedChunk

    return [
        RetrievedChunk(doc_id="d1", text="FastAPI is a Python web framework.", score=0.9, source="docs/intro.md"),
        RetrievedChunk(doc_id="d2", text="Qdrant is a vector database.", score=0.6, source="docs/vector.md"),
        RetrievedChunk(doc_id="d3", text="Redis is used as a cache layer.", score=0.4, source="docs/cache.md"),
    ]
