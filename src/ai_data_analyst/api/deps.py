"""API dependencies."""

from __future__ import annotations

from ai_data_analyst.config import Settings, get_settings
from ai_data_analyst.security.rate_limit import RateLimiter

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
