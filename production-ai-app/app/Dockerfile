FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /build
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1

COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /opt/venv && uv pip install --python /opt/venv/bin/python -r pyproject.toml

FROM python:3.12-slim-bookworm AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN groupadd --system app && useradd --system --gid app --home /app --shell /usr/sbin/nologin app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=app:app app ./app
COPY --chown=app:app components ./components
COPY --chown=app:app services ./services
COPY --chown=app:app prompts ./prompts
COPY --chown=app:app agents ./agents
COPY --chown=app:app security ./security
COPY --chown=app:app observability ./observability
COPY --chown=app:app evaluation ./evaluation

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
