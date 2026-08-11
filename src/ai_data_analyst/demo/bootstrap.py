"""Ensure a DuckDB analytics file exists for demos (Streamlit / Docker)."""

from __future__ import annotations

from pathlib import Path

from ai_data_analyst.config import Settings, get_settings
from ai_data_analyst.data.ingestion.olist import ingest_olist


def ensure_demo_database(settings: Settings | None = None) -> Path:
    """Return a usable DuckDB path, building from fixtures if needed.

    Preference order:
    1. Configured ``duckdb_path`` if it already exists and is non-empty
    2. Bundled ``data/demo/analytics.duckdb``
    3. Ingest ``tests/fixtures/olist`` into the demo path
    """
    settings = settings or get_settings()
    primary = settings.duckdb_path
    if primary.exists() and primary.stat().st_size > 0:
        return primary

    demo = settings.demo_duckdb_path
    if demo.exists() and demo.stat().st_size > 0:
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
