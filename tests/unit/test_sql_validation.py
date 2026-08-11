import pytest

from ai_data_analyst.tools.sql_validation import SQLValidationError, validate_sql


def test_validate_select_ok() -> None:
    assert validate_sql("SELECT 1") == "SELECT 1"


def test_validate_with_ok() -> None:
    sql = "WITH x AS (SELECT 1 AS n) SELECT n FROM x"
    assert validate_sql(sql) == sql


def test_validate_strips_comments_and_semicolon() -> None:
    assert validate_sql("SELECT 1; -- trailing") == "SELECT 1"


def test_rejects_drop() -> None:
    with pytest.raises(SQLValidationError):
        validate_sql("DROP TABLE orders")


def test_rejects_multiple_statements() -> None:
    with pytest.raises(SQLValidationError):
        validate_sql("SELECT 1; SELECT 2")


def test_rejects_insert() -> None:
    with pytest.raises(SQLValidationError):
        validate_sql("INSERT INTO orders VALUES (1)")
