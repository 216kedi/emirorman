"""RAGAS evaluation pipeline over the golden dataset."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.logging import get_logger

log = get_logger(__name__)

GOLDEN_PATH = Path(__file__).parent / "golden_dataset.json"


def load_golden() -> list[dict[str, Any]]:
    with GOLDEN_PATH.open() as f:
        return json.load(f)["items"]


def build_ragas_dataset(
    items: list[dict[str, Any]],
    pipeline_fn,
) -> "datasets.Dataset":
    """Run pipeline_fn on each golden item and build a RAGAS-compatible Dataset."""
    import asyncio

    from datasets import Dataset

    rows: list[dict] = []
    for item in items:
        result = asyncio.run(pipeline_fn(item["query"]))
        rows.append({
            "question": item["query"],
            "answer": result.get("answer", ""),
            "contexts": result.get("contexts", []),
            "ground_truth": item.get("expected_answer", ""),
        })
    return Dataset.from_list(rows)


async def run(pipeline_fn=None, output_dir: Path = Path("evaluation/eval_results")) -> dict[str, float]:
    """
    Runs RAGAS metrics against the golden dataset.

    pipeline_fn receives a query string and must return
    {"answer": str, "contexts": list[str]}.
    If pipeline_fn is None, loads saved results from eval_results/.
    """
    try:
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness
    except ImportError:
        log.warning("ragas_not_installed", hint="uv sync --group eval")
        return {}

    output_dir.mkdir(parents=True, exist_ok=True)
    items = load_golden()

    if pipeline_fn is None:
        log.warning("ragas_no_pipeline_fn", hint="Pass a pipeline_fn to generate live results")
        return {}

    dataset = build_ragas_dataset(items, pipeline_fn)
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
    )
    scores = {k: float(v) for k, v in result.items()}

    import json as _json
    out = output_dir / "ragas_latest.json"
    out.write_text(_json.dumps(scores, indent=2))
    log.info("ragas_done", scores=scores, output=str(out))
    return scores


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
