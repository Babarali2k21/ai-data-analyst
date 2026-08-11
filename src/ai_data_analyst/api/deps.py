"""API dependencies — composition root for settings, auth, rate limits."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request

from ai_data_analyst.config import Settings, get_settings
from ai_data_analyst.security.auth import require_api_key
from ai_data_analyst.security.errors import SecurityError
from ai_data_analyst.security.rate_limit import RateLimiter, client_key

_rate_limiter: RateLimiter | None = None


def settings_dep() -> Settings:
    return get_settings()


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    settings = get_settings()
    if (
        _rate_limiter is None
        or _rate_limiter.limit != settings.api_rate_limit_per_minute
    ):
        _rate_limiter = RateLimiter(
            limit=settings.api_rate_limit_per_minute, window_seconds=60
        )
    return _rate_limiter


def reset_rate_limiter() -> None:
    """Clear the singleton (used in tests when settings change)."""
    global _rate_limiter
    _rate_limiter = None


def enforce_access(
    request: Request,
    settings: Annotated[Settings, Depends(settings_dep)],
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str | None:
    """Validate API key and rate limit; map security errors to HTTP."""
    try:
        presented = require_api_key(
            settings, authorization=authorization, x_api_key=x_api_key
        )
        host = request.client.host if request.client else None
        get_rate_limiter().check(client_key(client_host=host, api_key=presented))
        return presented
    except SecurityError as exc:
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
            headers=headers,
        ) from exc
