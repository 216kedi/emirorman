from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.dependencies import shutdown as deps_shutdown
from app.errors import AppError, app_error_handler, unhandled_exception_handler
from app.logging import configure_logging, get_logger
from app.middleware import CorrelationMiddleware
from app.routes import alerts, feedback, health, metrics, query
from observability.tracer import setup_tracing

log = get_logger(__name__)

limiter = Limiter(
    key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    setup_tracing()
    log.info("app_starting", environment=settings.environment, version=settings.version)
    Instrumentator().instrument(app).expose(
        app, endpoint="/metrics/process", include_in_schema=False
    )
    try:
        yield
    finally:
        log.info("app_stopping")
        await deps_shutdown()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    app.state.limiter = limiter
    app.add_middleware(CorrelationMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(health.router)
    app.include_router(query.router)
    app.include_router(metrics.router)
    app.include_router(feedback.router)
    app.include_router(alerts.router)
    return app


app = create_app()
