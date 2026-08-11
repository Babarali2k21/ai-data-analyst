from pathlib import Path

from ai_data_analyst.config import Settings
from ai_data_analyst.data.duckdb import fetchdf, list_tables
from ai_data_analyst.data.ingestion.olist import ingest_olist
from ai_data_analyst.data.profiling.profiler import profile_database, write_profile

EXPECTED_TABLES = {
    "orders",
    "customers",
    "order_items",
    "order_payments",
    "order_reviews",
    "products",
    "sellers",
    "product_category_translation",
}


def test_ingest_fixtures_creates_tables(temp_settings: Settings) -> None:
    counts = ingest_olist(settings=temp_settings)
    assert set(counts) == EXPECTED_TABLES
    assert counts["orders"] == 3
    assert counts["order_items"] == 3
    assert counts["customers"] == 2

    tables = list_tables(path=temp_settings.duckdb_path)
    assert set(tables) == EXPECTED_TABLES

    df = fetchdf(
        """
        SELECT o.order_id, count(i.order_item_id) AS items
        FROM orders o
        JOIN order_items i ON o.order_id = i.order_id
        GROUP BY 1
        ORDER BY 1
        """,
        path=temp_settings.duckdb_path,
        read_only=True,
    )
    assert len(df) == 2
    assert int(df.loc[df["order_id"] == "o2", "items"].iloc[0]) == 2


def test_ingest_is_idempotent(temp_settings: Settings) -> None:
    first = ingest_olist(settings=temp_settings)
    second = ingest_olist(settings=temp_settings)
    assert first == second


def test_profiler_writes_json(temp_settings: Settings, tmp_path: Path) -> None:
    ingest_olist(settings=temp_settings)
    profile = profile_database(settings=temp_settings)
    assert set(profile["tables"]) == EXPECTED_TABLES
    assert profile["tables"]["orders"]["row_count"] == 3
    assert "order_id" in profile["tables"]["orders"]["columns"]
    assert "approx_distinct" in profile["tables"]["orders"]["columns"]["order_id"]
    assert "min" in profile["tables"]["order_items"]["columns"]["price"]

    out = tmp_path / "profile.json"
    written = write_profile(profile, out, settings=temp_settings)
    assert written.exists()
    assert written.read_text(encoding="utf-8").startswith("{")
