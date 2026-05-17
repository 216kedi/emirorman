"""FastAPI entry point for the production AI app."""
from fastapi import FastAPI

from app.config import settings
from app.models import QueryRequest, QueryResponse

app = FastAPI(title=settings.app_name, version=settings.version)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    raise NotImplementedError("Wire up the RAG pipeline in services/rag_pipeline.py")
