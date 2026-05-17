"""Pluggable tool: search a code corpus / repo index."""


class CodeSearchTool:
    name = "code_search"
    description = "Search indexed source code repositories."

    def __call__(self, query: str, top_k: int = 5) -> list[dict]:
        raise NotImplementedError
