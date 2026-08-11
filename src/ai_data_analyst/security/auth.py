"""API authentication (optional shared API keys). Framework-agnostic."""

from __future__ import annotations

from ai_data_analyst.config import Settings
from ai_data_analyst.security.errors import AuthenticationError


def extract_api_key(
    authorization: str | None,
    x_api_key: str | None,
) -> str | None:
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def require_api_key(
    settings: Settings,
    *,
    authorization: str | None = None,
    x_api_key: str | None = None,
) -> str | None:
    """Validate client API key when settings.api_keys is non-empty.

    Returns the presented key (or None when auth is disabled).
    Raises AuthenticationError when configured keys reject the request.
    """
    configured = [k.strip() for k in settings.api_keys if k.strip()]
    if not configured:
        return None

    presented = extract_api_key(authorization, x_api_key)
    if not presented or presented not in configured:
        raise AuthenticationError(
            "Invalid or missing API key. Provide X-API-Key or Authorization: Bearer <key>."
        )
    return presented
