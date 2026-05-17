from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sse_starlette.sse import EventSourceResponse

from app.auth import require_api_key
from app.config import settings
from app.dependencies import get_pipeline
from app.models import QueryRequest, QueryResponse
from services.rag_pipeline import RAGPipeline

router = APIRouter(tags=["query"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/query", response_model=QueryResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def query(
    request: Request,
    body: QueryRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
    _key: str = Depends(require_api_key),
) -> QueryResponse:
    return await pipeline.run(body, trace_id=request.state.trace_id)


@router.post("/query/stream")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def query_stream(
    request: Request,
    body: QueryRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
    _key: str = Depends(require_api_key),
) -> EventSourceResponse:
    async def event_source():
        async for token in pipeline.stream(body, trace_id=request.state.trace_id):
            yield {"event": "token", "data": token}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_source())
