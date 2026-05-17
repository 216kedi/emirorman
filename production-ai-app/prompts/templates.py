from dataclasses import dataclass, field


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    template: str
    cacheable: bool = False
    tags: tuple[str, ...] = field(default_factory=tuple)

    def render(self, **kwargs: object) -> str:
        return self.template.format(**kwargs)


RAG_ANSWER_V1 = PromptTemplate(
    name="rag_answer",
    version="v1",
    cacheable=True,
    tags=("rag", "answer"),
    template=(
        "You are a careful assistant. Answer ONLY using the context below. "
        "If the context is insufficient, say so explicitly. "
        "Cite passages inline as [1], [2], ...\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    ),
)

QUERY_REWRITE_V1 = PromptTemplate(
    name="query_rewrite",
    version="v1",
    tags=("rewriting",),
    template="Rewrite the user query for retrieval. Preserve intent.\nQuery: {query}\nRewritten:",
)
