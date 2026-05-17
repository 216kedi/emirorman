FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY app ./app
COPY components ./components
COPY services ./services
COPY prompts ./prompts
COPY agents ./agents
COPY security ./security
COPY observability ./observability

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
