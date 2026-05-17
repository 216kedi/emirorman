"""Semantic cache to short-circuit duplicate / near-duplicate queries."""


class SemanticCache:
    def __init__(self, embedder, store, threshold: float = 0.93) -> None:
        self.embedder = embedder
        self.store = store
        self.threshold = threshold

    def get(self, query: str) -> str | None:
        raise NotImplementedError

    def put(self, query: str, answer: str) -> None:
        raise NotImplementedError
