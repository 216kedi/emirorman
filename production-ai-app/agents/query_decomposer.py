"""Decompose complex queries into focused sub-queries."""


class QueryDecomposer:
    def __init__(self, llm) -> None:
        self.llm = llm

    def decompose(self, query: str) -> list[str]:
        raise NotImplementedError
