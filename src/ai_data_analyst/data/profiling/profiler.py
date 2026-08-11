"""Profile DuckDB tables and write datasets/olist/profile.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_data_analyst.config import Settings, get_settings
from ai_data_analyst.data.duckdb import get_connection, list_tables
from ai_data_analyst.data.ingestion.olist import load_schema

_NUMERIC_TYPES = frozenset({"INTEGER", "BIGINT", "DOUBLE"})
_TIMESTAMP_TYPES = frozenset({"TIMESTAMP"})
_CATEGORICAL_HINTS = (
    "status",
    "type",
    "state",
    "city",
    "category",
    "score",
)


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _is_key_or_categorical(column_name: str) -> bool:
    lower = column_name.lower()
    if lower.endswith("_id") or lower.endswith("_unique_id"):
        return True
    return any(hint in lower for hint in _CATEGORICAL_HINTS)


def profile_table(
    connection: Any,
    table_name: str,
    columns: list[dict[str, str]],
) -> dict[str, Any]:
    """Compute row count, nulls, distincts, and min/max for one table."""
    quoted = _quote_ident(table_name)
    row_count_row = connection.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()
    row_count = int(row_count_row[0]) if row_count_row else 0

    column_profiles: dict[str, Any] = {}
    for col in columns:
        name = col["name"]
        col_type = col["type"].upper()
        qcol = _quote_ident(name)

        null_row = connection.execute(
            f"SELECT COUNT(*) FILTER (WHERE {qcol} IS NULL) FROM {quoted}"
        ).fetchone()
        null_count = int(null_row[0]) if null_row else 0

        profile: dict[str, Any] = {
            "type": col_type,
            "null_count": null_count,
        }

        if _is_key_or_categorical(name):
            distinct_row = connection.execute(
                f"SELECT approx_count_distinct({qcol}) FROM {quoted}"
            ).fetchone()
            profile["approx_distinct"] = int(distinct_row[0]) if distinct_row else 0

        if col_type in _NUMERIC_TYPES or col_type in _TIMESTAMP_TYPES:
            stats = connection.execute(f"SELECT min({qcol}), max({qcol}) FROM {quoted}").fetchone()
            if stats:
                profile["min"] = None if stats[0] is None else str(stats[0])
                profile["max"] = None if stats[1] is None else str(stats[1])

        column_profiles[name] = profile

    return {"row_count": row_count, "columns": column_profiles}


def profile_database(
    *,
    settings: Settings | None = None,
    duckdb_path: Path | None = None,
    metadata_dir: Path | None = None,
) -> dict[str, Any]:
    """Profile all tables present in DuckDB that appear in schema.yaml."""
    settings = settings or get_settings()
    duckdb_path = duckdb_path or settings.duckdb_path
    metadata_dir = metadata_dir or settings.olist_metadata_dir
    schema = load_schema(metadata_dir)

    con = get_connection(read_only=True, path=duckdb_path, settings=settings)
    try:
        existing = set(list_tables(con))
        tables_out: dict[str, Any] = {}
        for table_name, table_schema in schema.items():
            if table_name not in existing:
                continue
            columns = table_schema["columns"]
            tables_out[table_name] = profile_table(con, table_name, columns)
    finally:
        con.close()

    return {"dataset": "olist", "tables": tables_out}


def write_profile(
    profile: dict[str, Any],
    output_path: Path | None = None,
    *,
    settings: Settings | None = None,
) -> Path:
    settings = settings or get_settings()
    output_path = output_path or (settings.olist_metadata_dir / "profile.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, sort_keys=True)
        f.write("\n")
    return output_path


def main() -> None:
    settings = get_settings()
    print(f"Profiling {settings.duckdb_path}")
    profile = profile_database(settings=settings)
    path = write_profile(profile, settings=settings)
    for name, table in sorted(profile["tables"].items()):
        print(f"  {name}: {table['row_count']:,} rows")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
