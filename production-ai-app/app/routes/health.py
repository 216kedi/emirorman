from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.version, "environment": settings.environment}


@router.get("/ready")
async def ready() -> dict[str, str]:
    return {"status": "ready"}
