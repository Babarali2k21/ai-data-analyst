"""Execute validated read-only SQL against DuckDB."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from ai_data_analyst.config import Settings, get_settings
from ai_data_analyst.data.duckdb import get_connection
from ai_data_analyst.observability.context import get_run_metrics
from ai_data_analyst.tools.sql_validation import validate_sql


class QueryResult(BaseModel):
    """Structured result from a SQL execution."""

    sql: str
    columns: list[str]
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int
    truncated: bool = False
    latency_ms: float = 0.0


def _apply_row_limit(sql: str, limit: int) -> str:
    """Wrap SQL so result size is bounded without relying on LLM LIMIT."""
    return f"SELECT * FROM ({sql}) AS _q LIMIT {int(limit)}"


def run_sql(
    query: str,
    *,
    settings: Settings | None = None,
    path: Path | None = None,
    row_limit: int | None = None,
) -> QueryResult:
    """Validate and execute a read-only SQL query, returning truncated rows."""
    settings = settings or get_settings()
    cleaned = validate_sql(query)
    limit = row_limit if row_limit is not None else settings.sql_row_limit
    limited_sql = _apply_row_limit(cleaned, limit)

    started = time.perf_counter()
    try:
        con = get_connection(read_only=True, path=path, settings=settings)
        try:
            df: pd.DataFrame = con.execute(limited_sql).fetchdf()
        finally:
            con.close()

        truncated = len(df) >= limit
        if truncated:
            con = get_connection(read_only=True, path=path, settings=settings)
            try:
                total = con.execute(f"SELECT COUNT(*) FROM ({cleaned}) AS _q").fetchone()
                total_count = int(total[0]) if total else len(df)
                truncated = total_count > limit
                row_count = total_count
            finally:
                con.close()
        else:
            row_count = len(df)

        records = df.where(pd.notnull(df), None).to_dict(orient="records")
        normalized: list[dict[str, Any]] = []
        for record in records:
            row: dict[str, Any] = {}
            for key, value in record.items():
                row[str(key)] = _jsonable(value)
            normalized.append(row)

        latency_ms = (time.perf_counter() - started) * 1000
        metrics = get_run_metrics()
        if metrics is not None:
            metrics.mark_sql(latency_ms, error=False)

        return QueryResult(
            sql=cleaned,
            columns=list(df.columns),
            rows=normalized,
            row_count=row_count,
            truncated=truncated,
            latency_ms=round(latency_ms, 2),
        )
    except Exception:
        latency_ms = (time.perf_counter() - started) * 1000
        metrics = get_run_metrics()
        if metrics is not None:
            metrics.mark_sql(latency_ms, error=True)
        raise


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
