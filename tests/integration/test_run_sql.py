from ai_data_analyst.config import Settings
from ai_data_analyst.data.ingestion.olist import ingest_olist
from ai_data_analyst.tools.sql import run_sql


def test_run_sql_on_fixtures(temp_settings: Settings) -> None:
    ingest_olist(settings=temp_settings)
    result = run_sql(
        "SELECT count(*) AS n FROM orders",
        settings=temp_settings,
        path=temp_settings.duckdb_path,
    )
    assert result.columns == ["n"]
    assert result.rows == [{"n": 3}]
    assert result.row_count == 1
    assert result.truncated is False


def test_run_sql_rejects_dangerous(temp_settings: Settings) -> None:
    ingest_olist(settings=temp_settings)
    try:
        run_sql("DELETE FROM orders", settings=temp_settings, path=temp_settings.duckdb_path)
        raised = False
    except Exception:
        raised = True
    assert raised
