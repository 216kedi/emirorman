import re


class ContentFilter:
    _patterns = [
        (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
        (re.compile(r"\b[0-9]{16}\b"), "[REDACTED_CC]"),
        (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[REDACTED_EMAIL]"),
        (re.compile(r"sk-[A-Za-z0-9]{20,}"), "[REDACTED_API_KEY]"),
    ]

    def filter(self, text: str) -> str:
        for pattern, replacement in self._patterns:
            text = pattern.sub(replacement, text)
        return text
