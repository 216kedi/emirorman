import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.logging import get_logger

log = get_logger(__name__)

TRACE_HEADER = "x-trace-id"


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get(TRACE_HEADER) or uuid.uuid4().hex
        request.state.trace_id = trace_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
        )

        start = time.perf_counter()
        log.info("request_started")
        try:
            response = await call_next(request)
        except Exception:
            log.exception("request_failed", duration_ms=(time.perf_counter() - start) * 1000)
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers[TRACE_HEADER] = trace_id
        log.info("request_completed", status_code=response.status_code, duration_ms=duration_ms)
        return response
