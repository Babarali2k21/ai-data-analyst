"""Framework-agnostic security errors (API maps these to HTTP)."""

from __future__ import annotations


class SecurityError(Exception):
    """Base class for auth / rate-limit failures."""

    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(SecurityError):
    def __init__(self, message: str = "Invalid or missing API key") -> None:
        super().__init__(message, status_code=401)


class RateLimitExceeded(SecurityError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=429)
