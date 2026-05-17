"""Output-side guard: hallucination / policy / leakage filtering."""
from security.input_guard import GuardResult


class OutputFilter:
    def check(self, answer: str, context: str) -> GuardResult:
        raise NotImplementedError
