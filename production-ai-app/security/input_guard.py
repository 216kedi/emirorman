import re
from dataclasses import dataclass


@dataclass
class GuardResult:
    allowed: bool
    reason: str | None = None


_INJECTION_PATTERNS = [
    re.compile(r"\bignore (all )?(previous|prior|above) instructions?\b", re.I),
    re.compile(r"\b(system prompt|developer prompt)\b", re.I),
    re.compile(r"<\|.*?(system|im_start).*?\|>", re.I),
]

_PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b[0-9]{16}\b"),
]


class InputGuard:
    def __init__(self, max_length: int = 8000) -> None:
        self.max_length = max_length

    def check(self, text: str) -> GuardResult:
        if not text or not text.strip():
            return GuardResult(False, "Empty query")
        if len(text) > self.max_length:
            return GuardResult(False, f"Query exceeds {self.max_length} chars")
        for pat in _INJECTION_PATTERNS:
            if pat.search(text):
                return GuardResult(False, "Possible prompt injection")
        for pat in _PII_PATTERNS:
            if pat.search(text):
                return GuardResult(False, "PII detected in query")
        return GuardResult(True)
