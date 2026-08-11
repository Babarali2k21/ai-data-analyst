"""Security helpers: auth and rate limiting (framework-agnostic)."""

from ai_data_analyst.security.auth import extract_api_key, require_api_key
from ai_data_analyst.security.errors import (
    AuthenticationError,
    RateLimitExceeded,
    SecurityError,
)
from ai_data_analyst.security.rate_limit import RateLimiter, client_key

__all__ = [
    "AuthenticationError",
    "RateLimitExceeded",
    "RateLimiter",
    "SecurityError",
    "client_key",
    "extract_api_key",
    "require_api_key",
]
