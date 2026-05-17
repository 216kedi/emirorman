from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.config import settings
from app.dependencies import shutdown as deps_shutdown
from app.errors import AppError, app_error_handler, unhandled_exception_handler
from app.logging import configure_logging, get_logger
from app.middleware import CorrelationMiddleware
from app.routes import health, query

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log.info("app_starting", environment=settings.environment, version=settings.version)
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
    )
    app.add_middleware(CorrelationMiddleware)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(health.router)
    app.include_router(query.router)
    return app


app = create_app()
