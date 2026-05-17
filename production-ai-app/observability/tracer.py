"""Per-stage tracing for the RAG / agent pipeline."""
from contextlib import contextmanager


class Tracer:
    def __init__(self, exporter=None) -> None:
        self.exporter = exporter

    @contextmanager
    def span(self, name: str, **attributes):
        raise NotImplementedError
