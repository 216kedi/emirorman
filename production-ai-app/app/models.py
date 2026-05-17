from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=8000)
    conversation_id: str | None = None
    stream: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    source: str
    score: float
    snippet: str


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    usd_cost: float = 0.0


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    trace_id: str
    cached: bool = False
    usage: Usage = Field(default_factory=Usage)


class ErrorResponse(BaseModel):
    error: str
    code: str
    trace_id: str | None = None
    detail: dict[str, Any] | None = None
