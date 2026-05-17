"""Pluggable tool: search the internal vector index."""


class VectorSearchTool:
    name = "vector_search"
    description = "Search internal knowledge base via embeddings."

    def __call__(self, query: str, top_k: int = 5) -> list[dict]:
        raise NotImplementedError
