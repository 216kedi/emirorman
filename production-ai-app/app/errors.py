from fastapi import Request, status
from fastapi.responses import ORJSONResponse

from app.logging import get_logger
from app.models import ErrorResponse

log = get_logger(__name__)


class AppError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"

    def __init__(self, message: str, detail: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class GuardrailBlocked(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "guardrail_blocked"


class UpstreamError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "upstream_error"


class RetrievalError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "retrieval_error"


class CacheUnavailable(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "cache_unavailable"


async def app_error_handler(request: Request, exc: AppError) -> ORJSONResponse:
    trace_id = getattr(request.state, "trace_id", None)
    log.error(
        "app_error",
        code=exc.code,
        message=exc.message,
        detail=exc.detail,
        trace_id=trace_id,
        path=request.url.path,
    )
    return ORJSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.message,
            code=exc.code,
            trace_id=trace_id,
            detail=exc.detail,
        ).model_dump(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    trace_id = getattr(request.state, "trace_id", None)
    log.exception("unhandled_exception", trace_id=trace_id, path=request.url.path)
    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            code="internal_error",
            trace_id=trace_id,
        ).model_dump(),
    )
