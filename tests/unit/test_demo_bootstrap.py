"""Tests for demo DuckDB bootstrap (Docker / AWS image)."""

from __future__ import annotations

from pathlib import Path

from ai_data_analyst.config import Settings
from ai_data_analyst.demo.bootstrap import ensure_demo_database


def test_ensure_demo_database_uses_bundled_or_fixtures(tmp_path: Path) -> None:
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
