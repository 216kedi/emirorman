# Deployment

## Local

```bash
docker compose up --build
```

- API: http://localhost:8000
- Frontend: http://localhost:8501

## Production

1. Build images: `docker build -f app/Dockerfile -t prod-ai-app:api .`
2. Push to your registry.
3. Apply Kubernetes manifests / Helm chart (not included in this template).
4. Run migrations: `python scripts/migrate.py`
5. Seed indices: `python scripts/seed.py`
6. Verify: `python scripts/healthcheck.py`
