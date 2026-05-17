"""User feedback capture (thumbs up/down, free-text, corrections)."""
from dataclasses import dataclass


@dataclass
class Feedback:
    trace_id: str
    rating: int
    comment: str | None = None


class FeedbackStore:
    def record(self, feedback: Feedback) -> None:
        raise NotImplementedError
