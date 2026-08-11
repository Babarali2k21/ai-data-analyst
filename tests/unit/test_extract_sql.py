from ai_data_analyst.analyst.sql_pipeline import extract_sql


def test_extract_raw_sql() -> None:
    assert extract_sql("SELECT 1") == "SELECT 1"


def test_extract_fenced_sql() -> None:
    text = "Here you go:\n```sql\nSELECT count(*) FROM orders\n```\n"
    assert extract_sql(text) == "SELECT count(*) FROM orders"
