"""
Rate limiting configuration using slowapi.

Uses Redis if REDIS_URL is configured, otherwise falls back to in-memory storage.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def _get_storage_uri() -> str:
    if settings.REDIS_URL:
        return settings.REDIS_URL
    return "memory://"


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT] if settings.RATE_LIMIT_ENABLED else [],
    storage_uri=_get_storage_uri(),
    enabled=settings.RATE_LIMIT_ENABLED,
)
