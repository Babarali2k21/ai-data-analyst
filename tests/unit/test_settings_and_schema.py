from pathlib import Path

from ai_data_analyst.config import Settings, get_settings
from ai_data_analyst.data.ingestion.olist import load_metadata, load_schema


def test_settings_defaults(tmp_path: Path, monkeypatch: object) -> None:
    # Ensure we don't pick up a local .env duckdb path unexpectedly for this check
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        duckdb_path=tmp_path / "analytics.duckdb",
        olist_raw_dir=tmp_path / "raw",
        olist_metadata_dir=tmp_path / "meta",
    )
    assert settings.llm_model == "gpt-4o-mini"
    assert settings.duckdb_path == tmp_path / "analytics.duckdb"


def test_get_settings_cached() -> None:
    get_settings.cache_clear()
    a = get_settings()
    b = get_settings()
    assert a is b
    get_settings.cache_clear()


def test_schema_yaml_loads(metadata_dir: Path) -> None:
    schema = load_schema(metadata_dir)
    expected = {
        "orders",
        "customers",
        "order_items",
        "order_payments",
        "order_reviews",
        "products",
        "sellers",
        "product_category_translation",
    }
    assert expected <= set(schema.keys())
    assert schema["orders"]["columns"][0]["name"] == "order_id"


def test_metadata_tables_match_schema(metadata_dir: Path) -> None:
    metadata = load_metadata(metadata_dir)
    schema = load_schema(metadata_dir)
    table_names = {t["name"] for t in metadata["tables"]}
    assert table_names == set(schema.keys())
    for table in metadata["tables"]:
        assert "file" in table
        assert "primary_key" in table
