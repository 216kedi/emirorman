"""Input-side guard: prompt injection, PII, abuse detection."""
from dataclasses import dataclass


@dataclass
class GuardResult:
    allowed: bool
    reason: str | None = None


class InputGuard:
    def check(self, text: str) -> GuardResult:
        raise NotImplementedError
