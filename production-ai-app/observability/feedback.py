from dataclasses import dataclass

from app.logging import get_logger
from observability.langfuse_client import score as langfuse_score

log = get_logger(__name__)


@dataclass
class Feedback:
    trace_id: str
    rating: int
    comment: str | None = None


class FeedbackStore:
    def record(self, feedback: Feedback) -> None:
        normalized = max(0.0, min(1.0, (feedback.rating - 1) / 4))
        langfuse_score(
            trace_id=feedback.trace_id,
            name="user_rating",
            value=normalized,
            comment=feedback.comment,
        )
        log.info("feedback_recorded", trace_id=feedback.trace_id, rating=feedback.rating)
