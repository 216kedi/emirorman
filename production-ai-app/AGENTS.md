# AGENTS.md

Guidance for agent-style coding assistants (Claude Code, Cursor, etc.).

## Workflow

1. Read `CLAUDE.md` for layout and conventions.
2. Read `claude/rules/code-style.md` and `claude/rules/testing.md` before writing code.
3. Add tests in `tests/` alongside any new module under `services/` or `components/`.
4. Never bypass `security/` guards — they run on every request.
5. New prompts go into `prompts/templates.py` with a version; register them in `prompts/registry.py`.

## Don't

- Don't put business logic in `app/` — keep it in `services/`.
- Don't hit external LLMs in unit tests.
- Don't commit secrets; use `app/config.py` + environment.
