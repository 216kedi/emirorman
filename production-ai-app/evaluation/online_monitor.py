"""Online evaluation: sample live traffic, score it, alert on regressions."""


class OnlineMonitor:
    def sample(self, trace_id: str) -> None:
        raise NotImplementedError

    def score(self, trace_id: str) -> dict:
        raise NotImplementedError
