"""Offline evaluation harness against the golden dataset."""
import json
from pathlib import Path

GOLDEN_PATH = Path(__file__).parent / "golden_dataset.json"


def load_golden() -> list[dict]:
    with GOLDEN_PATH.open() as f:
        return json.load(f)["items"]


def run() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    run()
