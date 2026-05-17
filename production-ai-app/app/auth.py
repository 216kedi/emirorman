import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings
from app.logging import get_logger

log = get_logger(__name__)

_API_KEY_HEADER = APIKeyHeader(name="x-api-key", auto_error=False)


def require_api_key(key: str | None = Security(_API_KEY_HEADER)) -> str:
    configured = settings.api_key
    if not configured:
        return "anonymous"
    if not key or not secrets.compare_digest(key, configured):
        log.warning("auth_failed", key_present=bool(key))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return key
