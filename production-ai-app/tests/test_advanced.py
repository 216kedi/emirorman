"""Phase 4 bileşenleri için birim testleri."""
import math

import pytest

from components.late_interaction import _cosine, _token_windows
from evaluation.trajectory_eval import (
    StepType,
    Trajectory,
    TrajectoryStep,
    summarize,
    TrajectoryEvalResult,
    TrajectoryScore,
)
from services.memory.episodic import Episode


# --- Late-interaction yardımcı testleri ---

def test_cosine_identical():
    v = [1.0, 2.0, 3.0]
    assert _cosine(v, v) == pytest.approx(1.0)


def test_cosine_orthogonal():
    assert _cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_token_windows_short_text():
    windows = _token_windows("hello world", window=64)
    assert windows == ["hello world"]


def test_token_windows_long_text():
    words = ["w"] * 200
    text = " ".join(words)
    windows = _token_windows(text, window=64, stride=32)
    assert len(windows) > 1
    for w in windows:
        assert len(w.split()) <= 64


# --- Trajectory testleri ---

def _make_result(composite: float) -> TrajectoryEvalResult:
    score = TrajectoryScore(
        strategy_score=composite,
        efficiency_score=composite,
        answer_quality=composite,
        reasoning="test",
    )
    return TrajectoryEvalResult(
        trace_id="t1",
        scores=score,
        step_count=3,
        total_latency_ms=500.0,
    )


def test_trajectory_composite_average():
    result = _make_result(0.8)
    assert result.composite == pytest.approx(0.8)


def test_trajectory_summarize_empty():
    assert summarize([]) == {}


def test_trajectory_summarize_metrics():
    results = [_make_result(0.6), _make_result(0.8)]
    summary = summarize(results)
    assert summary["n"] == 2
    assert summary["avg_composite"] == pytest.approx(0.7, abs=1e-3)


def test_trajectory_step_count():
    steps = [
        TrajectoryStep(step_type=StepType.ROUTE, input="q", output="rag"),
        TrajectoryStep(step_type=StepType.RETRIEVE, input="q", output="5 chunks"),
    ]
    traj = Trajectory(trace_id="t", query="q", steps=steps, final_answer="A")
    assert traj.step_count == 2
    assert len(traj.steps_of_type(StepType.ROUTE)) == 1


# --- Episodik memory testleri ---

def test_episode_serialization():
    ep = Episode(summary="Test summary", timestamp=1234567890.0)
    d = ep.to_dict()
    ep2 = Episode.from_dict(d)
    assert ep2.summary == ep.summary
    assert ep2.timestamp == ep.timestamp
