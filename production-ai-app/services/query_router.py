"""Route incoming queries to the right pipeline / model / toolset."""
from enum import Enum


class Route(str, Enum):
    SIMPLE_LOOKUP = "simple_lookup"
    RAG = "rag"
    AGENTIC = "agentic"


class QueryRouter:
    def __init__(self, llm) -> None:
        self.llm = llm

    def route(self, query: str) -> Route:
        raise NotImplementedError
