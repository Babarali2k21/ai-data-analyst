"""Validate SQL before execution against DuckDB."""

from __future__ import annotations

import re

_FORBIDDEN = re.compile(
    r"\b("
    r"INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|MERGE|"
    r"ATTACH|DETACH|COPY|EXPORT|IMPORT|INSTALL|LOAD|PRAGMA|SET|CALL|"
    r"GRANT|REVOKE|VACUUM|CHECKPOINT"
    r")\b",
    re.IGNORECASE,
)

_COMMENT_LINE = re.compile(r"--.*?$", re.MULTILINE)
_COMMENT_BLOCK = re.compile(r"/\*.*?\*/", re.DOTALL)


class SQLValidationError(ValueError):
    """Raised when a SQL statement fails safety checks."""


def strip_sql_comments(sql: str) -> str:
    sql = _COMMENT_BLOCK.sub(" ", sql)
    sql = _COMMENT_LINE.sub(" ", sql)
    return sql.strip()


def validate_sql(sql: str) -> str:
    """Ensure SQL is a single read-only SELECT/WITH query.

    Returns the cleaned SQL (comments stripped, trailing semicolon removed).
    """
    cleaned = strip_sql_comments(sql)
    if not cleaned:
        raise SQLValidationError("SQL is empty")

    # Allow one trailing semicolon only
    if ";" in cleaned.rstrip(";"):
        raise SQLValidationError("Only a single SQL statement is allowed")
    cleaned = cleaned.rstrip(";").strip()

    if _FORBIDDEN.search(cleaned):
        raise SQLValidationError("Only read-only SELECT/WITH queries are allowed")

    first = cleaned.lstrip().split(None, 1)[0].upper()
    if first not in {"SELECT", "WITH"}:
        raise SQLValidationError("Query must start with SELECT or WITH")

    return cleaned
