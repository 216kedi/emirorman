"""LLM-driven adaptive routing across tools and knowledge sources."""
from agents.tools.vector_search import VectorSearchTool
from agents.tools.web_search import WebSearchTool
from agents.tools.code_search import CodeSearchTool


class AdaptiveRouter:
    def __init__(self, llm, tools: list | None = None) -> None:
        self.llm = llm
        self.tools = tools or [VectorSearchTool(), WebSearchTool(), CodeSearchTool()]

    def select_tool(self, query: str):
        raise NotImplementedError
