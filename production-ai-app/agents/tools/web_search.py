"""Pluggable tool: search the live web."""


class WebSearchTool:
    name = "web_search"
    description = "Search the public web for current information."

    def __call__(self, query: str, top_k: int = 5) -> list[dict]:
        raise NotImplementedError
