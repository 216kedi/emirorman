from functools import lru_cache
from typing import Any

from app.config import settings
from app.logging import get_logger

log = get_logger(__name__)


@lru_cache
def get_langfuse():
    if not settings.langfuse_public_key:
        return None
    try:
        from langfuse import Langfuse

        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception as e:
        log.warning("langfuse_init_failed", error=str(e))
        return None


def trace_generation(
    trace_id: str,
    name: str,
    input: Any,
    output: Any,
    model: str | None = None,
    usage: dict | None = None,
) -> None:
    lf = get_langfuse()
    if lf is None:
        return
    try:
        t = lf.trace(id=trace_id, name=name)
        t.generation(
            name=name,
            input=input,
            output=output,
            model=model,
            usage=usage,
        )
    except Exception as e:
        log.warning("langfuse_trace_failed", error=str(e))


def score(trace_id: str, name: str, value: float, comment: str | None = None) -> None:
    lf = get_langfuse()
    if lf is None:
        return
    try:
        lf.score(trace_id=trace_id, name=name, value=value, comment=comment)
    except Exception as e:
        log.warning("langfuse_score_failed", error=str(e))
