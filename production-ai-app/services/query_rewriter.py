"""LLM-driven query rewriting for retrieval quality."""


class QueryRewriter:
    def __init__(self, llm) -> None:
        self.llm = llm

    def rewrite(self, query: str, history: list[str] | None = None) -> str:
        raise NotImplementedError
