from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth import require_api_key
from observability.feedback import Feedback, FeedbackStore

router = APIRouter(tags=["feedback"])
_store = FeedbackStore()


class FeedbackRequest(BaseModel):
    trace_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


@router.post("/feedback", status_code=204)
async def submit_feedback(
    body: FeedbackRequest,
    _key: str = Depends(require_api_key),
) -> None:
    _store.record(Feedback(trace_id=body.trace_id, rating=body.rating, comment=body.comment))
