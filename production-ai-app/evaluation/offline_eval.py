"""Offline evaluation runner: retrieval metrics + LLM-as-judge + RAGAS."""
from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

from app.logging import configure_logging, get_logger
from evaluation.llm_judge import LLMJudge, JudgeResult
from evaluation.metrics import RetrievalMetrics, compute_all

log = get_logger(__name__)
console = Console()

GOLDEN_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_DIR = Path(__file__).parent / "eval_results"


@dataclass
class EvalRecord:
    item_id: str
    query: str
    answer: str
    retrieval: RetrievalMetrics
    judge: JudgeResult

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "query": self.query,
            "answer": self.answer[:300],
            "recall_at_5": self.retrieval.recall_at_k,
            "ndcg_at_5": self.retrieval.ndcg_at_k,
            "mrr": self.retrieval.mrr,
            "faithfulness": self.judge.faithfulness,
            "relevance": self.judge.relevance,
            "correctness": self.judge.correctness,
            "composite": self.judge.composite,
        }


def load_golden() -> list[dict]:
    with GOLDEN_PATH.open() as f:
        return json.load(f)["items"]


def _print_table(records: list[EvalRecord]) -> None:
    table = Table(title="Offline Evaluation Results", show_lines=True)
    for col in ("ID", "Recall@5", "nDCG@5", "MRR", "Faith.", "Rel.", "Correct.", "Composite"):
        table.add_column(col, justify="right")
    for r in records:
        table.add_row(
            r.item_id,
            f"{r.retrieval.recall_at_k:.3f}",
            f"{r.retrieval.ndcg_at_k:.3f}",
            f"{r.retrieval.mrr:.3f}",
            f"{r.judge.faithfulness:.3f}",
            f"{r.judge.relevance:.3f}",
            f"{r.judge.correctness:.3f}" if r.judge.correctness is not None else "—",
            f"{r.judge.composite:.3f}",
        )
    console.print(table)


async def run_item(
    item: dict,
    judge: LLMJudge,
    pipeline_fn,
) -> EvalRecord:
    result = await pipeline_fn(item["query"])
    retrieved_ids: list[str] = result.get("retrieved_ids", [])
    relevant_ids: list[str] = item.get("expected_sources", [])

    retrieval_metrics = compute_all(retrieved_ids, relevant_ids, k=5)

    context = "\n".join(result.get("contexts", []))
    judge_result = await judge.judge(
        query=item["query"],
        context=context,
        answer=result.get("answer", ""),
        reference=item.get("expected_answer"),
    )

    return EvalRecord(
        item_id=item["id"],
        query=item["query"],
        answer=result.get("answer", ""),
        retrieval=retrieval_metrics,
        judge=judge_result,
    )


async def run(pipeline_fn=None) -> list[EvalRecord]:
    configure_logging()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    items = load_golden()

    if pipeline_fn is None:
        log.warning("offline_eval_no_pipeline", hint="Pass pipeline_fn(query) -> dict")
        return []

    judge = LLMJudge()
    records = await asyncio.gather(*[run_item(item, judge, pipeline_fn) for item in items])
    records = list(records)

    _print_table(records)

    out = RESULTS_DIR / "offline_latest.json"
    out.write_text(json.dumps([r.to_dict() for r in records], indent=2))
    log.info("offline_eval_done", output=str(out), items=len(records))
    return records


if __name__ == "__main__":
    asyncio.run(run())
