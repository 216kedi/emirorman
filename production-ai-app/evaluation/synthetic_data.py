"""Synthetic golden dataset generator via LLM.

Verilen bir döküman korpusundan otomatik soru-cevap çiftleri üretir.
Bu çiftler golden_dataset.json'a eklenebilir ya da RAGAS için kullanılabilir.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

import instructor
from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

from app.config import settings
from app.logging import configure_logging, get_logger

log = get_logger(__name__)


class QAPair(BaseModel):
    question: str = Field(..., min_length=10)
    answer: str = Field(..., min_length=20)
    source_excerpt: str = Field(..., min_length=10)
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    tags: list[str] = Field(default_factory=list)


class QASet(BaseModel):
    pairs: list[QAPair] = Field(..., min_length=1)


_SYSTEM = (
    "You are a dataset curator. Given a document excerpt, generate diverse "
    "question-answer pairs that test comprehension at varying difficulty levels. "
    "Questions should be specific and answerable purely from the excerpt. "
    "Return structured JSON only."
)


class SyntheticDataGenerator:
    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.default_llm_model
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.client = instructor.from_anthropic(client)

    async def generate_from_text(self, text: str, source: str, n: int = 5) -> list[dict]:
        result: QASet = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"Document (source: {source}):\n{text}\n\nGenerate {n} QA pairs.",
            }],
            response_model=QASet,
        )

        items = []
        for pair in result.pairs:
            items.append({
                "id": f"syn-{uuid.uuid4().hex[:8]}",
                "query": pair.question,
                "expected_answer": pair.answer,
                "expected_sources": [source],
                "tags": [*pair.tags, pair.difficulty, "synthetic"],
            })
        return items

    async def generate_from_files(self, paths: list[Path], n_per_file: int = 5) -> list[dict]:
        tasks = [
            self.generate_from_text(p.read_text()[:3000], source=str(p), n=n_per_file)
            for p in paths
            if p.exists() and p.suffix in {".md", ".txt", ".rst"}
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        items: list[dict] = []
        for r in results:
            if isinstance(r, Exception):
                log.warning("synthetic_gen_failed", error=str(r))
            else:
                items.extend(r)
        return items


async def main() -> None:
    configure_logging()
    generator = SyntheticDataGenerator()
    doc_paths = list(Path("docs").glob("*.md"))

    if not doc_paths:
        log.warning("no_docs_found", path="docs/")
        return

    items = await generator.generate_from_files(doc_paths, n_per_file=3)
    output = Path("evaluation/golden_dataset_synthetic.json")
    output.write_text(json.dumps({"version": "synthetic", "items": items}, indent=2))
    log.info("synthetic_done", count=len(items), output=str(output))


if __name__ == "__main__":
    asyncio.run(main())
