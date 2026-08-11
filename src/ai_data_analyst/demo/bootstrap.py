"""Ensure a DuckDB analytics file exists for Docker images / tests."""

from __future__ import annotations

from pathlib import Path

from ai_data_analyst.config import Settings, get_settings
from ai_data_analyst.data.duckdb import is_duckdb_ready
from ai_data_analyst.data.ingestion.olist import ingest_olist


def ensure_demo_database(settings: Settings | None = None) -> Path:
    """Return a usable DuckDB path, building from fixtures if needed.

    Preference order:
    1. Configured ``duckdb_path`` if ready
    2. Bundled ``data/demo/analytics.duckdb``
    3. Ingest ``tests/fixtures/olist`` into the demo path

    Containers set ``DUCKDB_PATH`` to the bundled demo DB (SSOT in Dockerfile).
    """
    settings = settings or get_settings()
    primary = settings.duckdb_path
    if is_duckdb_ready(primary):
        return primary

    demo = settings.demo_duckdb_path
    if is_duckdb_ready(demo):
        return demo

    fixtures = settings.repo_root / "tests" / "fixtures" / "olist"
    if not fixtures.exists():
        raise FileNotFoundError(
            f"No DuckDB at {primary} and no fixtures at {fixtures}. "
            "Run: make ingest"
        )

    demo.parent.mkdir(parents=True, exist_ok=True)
    settings.charts_dir.mkdir(parents=True, exist_ok=True)
    ingest_olist(
        settings=settings,
        raw_dir=fixtures,
        duckdb_path=demo,
        metadata_dir=settings.olist_metadata_dir,
    )
    return demo
