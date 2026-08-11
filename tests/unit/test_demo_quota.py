"""Tests for demo query quota and DuckDB bootstrap."""

from __future__ import annotations

from pathlib import Path

from ai_data_analyst.config import Settings
from ai_data_analyst.demo.bootstrap import ensure_demo_database
from ai_data_analyst.security.demo_quota import (
    DemoQuotaStore,
    fingerprint_visitor,
)


def test_fingerprint_is_stable() -> None:
    a = fingerprint_visitor(ip="1.2.3.4", cookie="abc")
    b = fingerprint_visitor(ip="1.2.3.4, 9.9.9.9", cookie="abc")
    assert a == b
    assert a != fingerprint_visitor(ip="1.2.3.4", cookie="other")


def test_quota_allows_three_then_blocks(tmp_path: Path) -> None:
    store = DemoQuotaStore(tmp_path / "quota.sqlite")
    vid = "visitor_a"
    for i in range(3):
        status = store.consume(vid, limit=3)
        assert status.allowed is True
        assert status.used == i + 1
        assert status.remaining == 3 - (i + 1)
    blocked = store.consume(vid, limit=3)
    assert blocked.allowed is False
    assert blocked.remaining == 0
    assert store.status(vid, limit=3).used == 3


def test_ensure_demo_database_uses_bundled_or_fixtures(
    tmp_path: Path, monkeypatch: object
) -> None:
    repo = Path(__file__).resolve().parents[2]
    settings = Settings(
        duckdb_path=tmp_path / "missing.duckdb",
        demo_duckdb_path=repo / "data" / "demo" / "analytics.duckdb",
        olist_raw_dir=repo / "tests" / "fixtures" / "olist",
        olist_metadata_dir=repo / "datasets" / "olist",
        charts_dir=tmp_path / "charts",
    )
    path = ensure_demo_database(settings)
    assert path.exists()
    assert path.stat().st_size > 0
