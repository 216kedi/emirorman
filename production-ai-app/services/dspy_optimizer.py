"""DSPy prompt optimizer.

BootstrapFewShot veya MIPROv2 ile RAGModule'ü golden dataset üzerinde
optimize eder. Üretilen program prompts/optimized/ altına kaydedilir
ve uygulama boot'ta yüklenebilir.

Çalıştır:
  uv run python -m services.dspy_optimizer --optimizer mipro --n-trials 10
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.config import settings
from app.logging import configure_logging, get_logger

log = get_logger(__name__)

OPTIMIZED_DIR = Path("prompts/optimized")


def _configure_dspy() -> None:
    import dspy

    lm = dspy.LM(
        model=f"anthropic/{settings.default_llm_model}",
        api_key=settings.anthropic_api_key,
        max_tokens=1024,
        cache=True,
    )
    dspy.configure(lm=lm)


def _load_trainset() -> list:
    import dspy

    golden_path = Path("evaluation/golden_dataset.json")
    items = json.loads(golden_path.read_text())["items"]
    trainset = []
    for item in items:
        trainset.append(
            dspy.Example(
                history="",
                question=item["query"],
                context="",
                answer=item["expected_answer"],
            ).with_inputs("history", "question", "context")
        )
    return trainset


def _faithfulness_metric(example, prediction, trace=None) -> float:
    answer = getattr(prediction, "answer", "") or ""
    expected = getattr(example, "answer", "") or ""
    if not expected:
        return 0.5
    overlap = len(set(answer.lower().split()) & set(expected.lower().split()))
    return min(1.0, overlap / max(len(expected.split()), 1))


async def optimize(optimizer_name: str = "bootstrap", n_trials: int = 5) -> None:
    import dspy
    from dspy.teleprompt import BootstrapFewShot

    configure_logging()
    _configure_dspy()

    from prompts.dspy_modules import RAGModule

    module = RAGModule()
    trainset = _load_trainset()

    if optimizer_name == "mipro":
        from dspy.teleprompt import MIPROv2

        optimizer = MIPROv2(metric=_faithfulness_metric, num_candidates=n_trials, init_temperature=1.0)
    else:
        optimizer = BootstrapFewShot(metric=_faithfulness_metric, max_bootstrapped_demos=4)

    log.info("dspy_optimize_start", optimizer=optimizer_name, trainset_size=len(trainset))
    compiled = optimizer.compile(module, trainset=trainset)

    OPTIMIZED_DIR.mkdir(parents=True, exist_ok=True)
    out = OPTIMIZED_DIR / f"rag_module_{optimizer_name}.json"
    compiled.save(str(out))
    log.info("dspy_optimize_done", output=str(out))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--optimizer", default="bootstrap", choices=["bootstrap", "mipro"])
    parser.add_argument("--n-trials", type=int, default=5)
    args = parser.parse_args()
    asyncio.run(optimize(args.optimizer, args.n_trials))


if __name__ == "__main__":
    main()
