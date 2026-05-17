"""Self-correcting retrieval: grade retrieved docs for relevance."""
from dataclasses import dataclass


@dataclass
class Grade:
    doc_id: str
    relevant: bool
    reason: str


class DocumentGrader:
    def __init__(self, llm) -> None:
        self.llm = llm

    def grade(self, query: str, docs: list[dict]) -> list[Grade]:
        raise NotImplementedError
