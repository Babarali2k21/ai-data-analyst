"""DuckDB connection helpers for the analytical database."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from ai_data_analyst.config import Settings, get_settings


def is_duckdb_ready(path: Path) -> bool:
    """True when the analytics DB file exists and is non-empty."""
    return path.exists() and path.stat().st_size > 0


def get_connection(
    *,
    read_only: bool = False,
    path: Path | None = None,
    settings: Settings | None = None,
) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection, creating parent directories when writing."""
    settings = settings or get_settings()
    db_path = path or settings.duckdb_path
    if not read_only:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # Replace empty placeholder files (e.g. gitkeep-era 0-byte .duckdb)
        if db_path.exists() and db_path.stat().st_size == 0:
            db_path.unlink()
    return duckdb.connect(str(db_path), read_only=read_only)


def execute(
    connection: duckdb.DuckDBPyConnection,
    sql: str,
    params: list[Any] | None = None,
) -> duckdb.DuckDBPyConnection:
    """Execute SQL on an existing connection and return the connection."""
    if params is None:
        connection.execute(sql)
    else:
        connection.execute(sql, params)
    return connection


def fetchdf(
    sql: str,
    params: list[Any] | None = None,
    *,
    connection: duckdb.DuckDBPyConnection | None = None,
    read_only: bool = True,
    path: Path | None = None,
) -> pd.DataFrame:
    """Execute SQL and return a pandas DataFrame."""
    owns_connection = connection is None
    con = connection or get_connection(read_only=read_only, path=path)
    try:
        if params is None:
            return con.execute(sql).fetchdf()
        return con.execute(sql, params).fetchdf()
    finally:
        if owns_connection:
            con.close()


def list_tables(
    connection: duckdb.DuckDBPyConnection | None = None,
    *,
    path: Path | None = None,
) -> list[str]:
    """Return user table names in the database."""
    owns_connection = connection is None
    con = connection or get_connection(read_only=True, path=path)
    try:
        rows = con.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main' AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        ).fetchall()
        return [str(row[0]) for row in rows]
    finally:
        if owns_connection:
            con.close()
