# Code Style

- Python 3.12+, type hints everywhere.
- Format with `ruff format`; lint with `ruff check`.
- Prefer dataclasses / Pydantic models over raw dicts at module boundaries.
- No comments restating what code does; only WHY when non-obvious.
- Module names: snake_case. Class names: PascalCase. Constants: UPPER_SNAKE.
