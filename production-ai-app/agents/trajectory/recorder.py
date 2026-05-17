"""Trajectory recorder — ajan adımlarını izlemek için lightweight context manager.

with TrajectoryRecorder(trace_id, query) as rec:
    rec.step(StepType.ROUTE, input=query, output=route)
    rec.step(StepType.RETRIEVE, input=query, output=f"{len(chunks)} chunks")
    ...
trajectory = rec.build(final_answer=answer)
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field

from evaluation.trajectory_eval import StepType, Trajectory, TrajectoryStep


class TrajectoryRecorder:
    def __init__(self, trace_id: str, query: str) -> None:
        self.trace_id = trace_id
        self.query = query
        self._steps: list[TrajectoryStep] = []
        self._step_start: float = 0.0

    def __enter__(self) -> "TrajectoryRecorder":
        return self

    def __exit__(self, *_) -> None:
        pass

    @contextmanager
    def timed_step(self, step_type: StepType, input: str):
        start = time.perf_counter()
        output_holder: list[str] = []
        yield output_holder
        latency_ms = (time.perf_counter() - start) * 1000
        self._steps.append(
            TrajectoryStep(
                step_type=step_type,
                input=input[:400],
                output=(output_holder[0] if output_holder else "")[:400],
                latency_ms=latency_ms,
            )
        )

    def step(self, step_type: StepType, input: str, output: str, latency_ms: float = 0.0) -> None:
        self._steps.append(
            TrajectoryStep(
                step_type=step_type,
                input=input[:400],
                output=output[:400],
                latency_ms=latency_ms,
            )
        )

    def build(self, final_answer: str, expected_answer: str | None = None) -> Trajectory:
        return Trajectory(
            trace_id=self.trace_id,
            query=self.query,
            steps=list(self._steps),
            final_answer=final_answer,
            expected_answer=expected_answer,
        )
