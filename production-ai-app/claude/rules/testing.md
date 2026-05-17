# Testing

- Framework: `pytest`.
- Each `services/` and `components/` module gets a sibling test in `tests/`.
- Use fakes / stubs for LLM and vector store calls — no live network in unit tests.
- Golden dataset evaluation lives in `evaluation/offline_eval.py` and runs in CI nightly.
- Coverage target: ≥ 80% on `services/` and `components/`.
