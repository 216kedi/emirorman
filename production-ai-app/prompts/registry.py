"""Hot-swappable prompt registry indexed by (name, version)."""
from prompts.templates import QUERY_REWRITE_V1, RAG_ANSWER_V1, PromptTemplate

_REGISTRY: dict[tuple[str, str], PromptTemplate] = {
    (RAG_ANSWER_V1.name, RAG_ANSWER_V1.version): RAG_ANSWER_V1,
    (QUERY_REWRITE_V1.name, QUERY_REWRITE_V1.version): QUERY_REWRITE_V1,
}


def get(name: str, version: str) -> PromptTemplate:
    return _REGISTRY[(name, version)]


def register(template: PromptTemplate) -> None:
    _REGISTRY[(template.name, template.version)] = template
