from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from app.dependencies import get_pipeline
from app.models import QueryRequest, QueryResponse
from services.rag_pipeline import RAGPipeline

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query(
    request: Request,
    body: QueryRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> QueryResponse:
    return await pipeline.run(body, trace_id=request.state.trace_id)


@router.post("/query/stream")
async def query_stream(
    request: Request,
    body: QueryRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> EventSourceResponse:
    async def event_source():
        async for token in pipeline.stream(body, trace_id=request.state.trace_id):
            yield {"event": "token", "data": token}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_source())
