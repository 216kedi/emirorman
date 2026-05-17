"""Mid-pipeline filter: redact PII / unsafe content in retrieved context."""


class ContentFilter:
    def filter(self, text: str) -> str:
        raise NotImplementedError
