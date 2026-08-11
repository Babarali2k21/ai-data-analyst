"""Persistent per-visitor demo query quota (token burn protection)."""

from __future__ import annotations

import hashlib
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from ai_data_analyst.config import Settings, get_settings

_lock = threading.Lock()


@dataclass(frozen=True)
class QuotaStatus:
    visitor_id: str
    used: int
    limit: int
    remaining: int
    allowed: bool


def fingerprint_visitor(*, ip: str | None, cookie: str | None) -> str:
    """Stable-ish visitor key from IP + optional browser cookie."""
    ip_part = (ip or "unknown").split(",")[0].strip() or "unknown"
    cookie_part = (cookie or "").strip() or "anon"
    digest = hashlib.sha256(f"{ip_part}|{cookie_part}".encode()).hexdigest()
    return digest[:24]


class DemoQuotaStore:
    """SQLite-backed counter. Survives Streamlit reruns; resets on container wipe."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS quotas (
                    visitor_id TEXT PRIMARY KEY,
                    used INTEGER NOT NULL DEFAULT 0,
                    updated_at REAL NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.path), timeout=10)
        con.execute("PRAGMA journal_mode=WAL")
        return con

    def status(self, visitor_id: str, *, limit: int) -> QuotaStatus:
        with _lock, self._connect() as con:
            row = con.execute(
                "SELECT used FROM quotas WHERE visitor_id = ?", (visitor_id,)
            ).fetchone()
        used = int(row[0]) if row else 0
        remaining = max(0, limit - used)
        return QuotaStatus(
            visitor_id=visitor_id,
            used=used,
            limit=limit,
            remaining=remaining,
            allowed=used < limit,
        )

    def consume(self, visitor_id: str, *, limit: int) -> QuotaStatus:
        """Atomically consume one query if under limit."""
        with _lock, self._connect() as con:
            row = con.execute(
                "SELECT used FROM quotas WHERE visitor_id = ?", (visitor_id,)
            ).fetchone()
            used = int(row[0]) if row else 0
            if used >= limit:
                return QuotaStatus(
                    visitor_id=visitor_id,
                    used=used,
                    limit=limit,
                    remaining=0,
                    allowed=False,
                )
            used += 1
            con.execute(
                """
                INSERT INTO quotas (visitor_id, used, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(visitor_id) DO UPDATE SET
                    used = excluded.used,
                    updated_at = excluded.updated_at
                """,
                (visitor_id, used, time.time()),
            )
            con.commit()
        remaining = max(0, limit - used)
        return QuotaStatus(
            visitor_id=visitor_id,
            used=used,
            limit=limit,
            remaining=remaining,
            allowed=True,
        )


def get_demo_quota_store(settings: Settings | None = None) -> DemoQuotaStore:
    settings = settings or get_settings()
    return DemoQuotaStore(settings.demo_quota_path)
