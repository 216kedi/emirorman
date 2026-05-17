import re

from security.input_guard import GuardResult


class OutputFilter:
    _refusal_markers = [
        re.compile(r"as an ai language model", re.I),
        re.compile(r"i cannot (assist|help|comply)", re.I),
    ]

    def __init__(self, min_grounding_overlap: int = 8) -> None:
        self.min_grounding_overlap = min_grounding_overlap

    def check(self, answer: str, context: str) -> GuardResult:
        if not answer or not answer.strip():
            return GuardResult(False, "Empty answer")
        for pat in self._refusal_markers:
            if pat.search(answer):
                return GuardResult(False, "Refusal-style output")
        if context.strip() and context != "(no context)":
            shared = self._token_overlap(answer, context)
            if shared < self.min_grounding_overlap:
                return GuardResult(False, "Answer not grounded in context")
        return GuardResult(True)

    @staticmethod
    def _token_overlap(answer: str, context: str) -> int:
        a = set(re.findall(r"\w{4,}", answer.lower()))
        c = set(re.findall(r"\w{4,}", context.lower()))
        return len(a & c)
