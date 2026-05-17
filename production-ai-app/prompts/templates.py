"""Versioned, type-specific prompt templates."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    template: str

    def render(self, **kwargs) -> str:
        return self.template.format(**kwargs)


RAG_ANSWER_V1 = PromptTemplate(
    name="rag_answer",
    version="v1",
    template=(
        "You are a careful assistant. Answer using ONLY the context below. "
        "Cite sources as [n].\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
    ),
)

QUERY_REWRITE_V1 = PromptTemplate(
    name="query_rewrite",
    version="v1",
    template="Rewrite the user query for retrieval. Preserve intent.\nQuery: {query}\nRewritten:",
)
