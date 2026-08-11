"""Simple in-memory sliding-window rate limiter. Framework-agnostic."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from ai_data_analyst.security.errors import RateLimitExceeded


class RateLimiter:
    def __init__(self, *, limit: int, window_seconds: int = 60) -> None:
        self.limit = max(1, limit)
        self.window_seconds = max(1, window_seconds)
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            bucket = self._hits[key]
            cutoff = now - self.window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.limit:
                raise RateLimitExceeded(
                    f"Rate limit exceeded: {self.limit} requests per "
                    f"{self.window_seconds}s"
                )
            bucket.append(now)


def client_key(*, client_host: str | None, api_key: str | None = None) -> str:
    if api_key:
        return f"key:{api_key[:8]}"
    return f"ip:{client_host or 'unknown'}"
