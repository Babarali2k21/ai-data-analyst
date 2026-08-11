"""Ingest Olist CSVs into DuckDB using datasets/olist metadata + schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ai_data_analyst.config import Settings, get_settings
from ai_data_analyst.data.duckdb import get_connection

# DuckDB type names used in schema.yaml
_VALID_TYPES = frozenset({"VARCHAR", "INTEGER", "BIGINT", "DOUBLE", "TIMESTAMP", "BOOLEAN"})


def load_metadata(metadata_dir: Path) -> dict[str, Any]:
    path = metadata_dir / "metadata.yaml"
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid metadata at {path}")
    return data


def load_schema(metadata_dir: Path) -> dict[str, Any]:
    path = metadata_dir / "schema.yaml"
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid schema at {path}")
    return data


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _csv_select_sql(csv_path: Path, columns: list[dict[str, str]]) -> str:
    """Build SELECT with explicit casts from read_csv (handles BOM via utf-8)."""
    casts: list[str] = []
    for col in columns:
        name = col["name"]
        col_type = col["type"].upper()
        if col_type not in _VALID_TYPES:
            raise ValueError(f"Unsupported column type {col_type!r} for {name}")
        casts.append(f"CAST({_quote_ident(name)} AS {col_type}) AS {_quote_ident(name)}")

    # utf-8 with BOM: DuckDB header_normalization + all_varchar then cast is safest;
    # read_csv with encoding utf-8 handles BOM on the first column name.
    csv_literal = str(csv_path.resolve()).replace("'", "''")
    select_list = ",\n           ".join(casts)
    return f"""
        SELECT {select_list}
        FROM read_csv(
            '{csv_literal}',
            header = true,
            auto_detect = true,
            ignore_errors = false,
            nullstr = '',
            encoding = 'utf-8'
        )
    """


def ingest_olist(
    *,
    settings: Settings | None = None,
    raw_dir: Path | None = None,
    duckdb_path: Path | None = None,
    metadata_dir: Path | None = None,
) -> dict[str, int]:
    """Load all configured Olist tables into DuckDB. Idempotent (CREATE OR REPLACE)."""
    settings = settings or get_settings()
    raw_dir = raw_dir or settings.olist_raw_dir
    metadata_dir = metadata_dir or settings.olist_metadata_dir
    duckdb_path = duckdb_path or settings.duckdb_path

    metadata = load_metadata(metadata_dir)
    schema = load_schema(metadata_dir)
    tables = metadata.get("tables")
    if not isinstance(tables, list) or not tables:
        raise ValueError("metadata.yaml must define a non-empty tables list")

    row_counts: dict[str, int] = {}
    con = get_connection(read_only=False, path=duckdb_path, settings=settings)
    try:
        for table in tables:
            name = table["name"]
            filename = table["file"]
            if name not in schema:
                raise KeyError(f"Table {name!r} missing from schema.yaml")
            columns = schema[name]["columns"]
            csv_path = raw_dir / filename
            if not csv_path.exists():
                raise FileNotFoundError(f"Missing CSV for {name}: {csv_path}")

            select_sql = _csv_select_sql(csv_path, columns)
            con.execute(f"CREATE OR REPLACE TABLE {_quote_ident(name)} AS {select_sql}")
            count = con.execute(f"SELECT COUNT(*) FROM {_quote_ident(name)}").fetchone()
            row_counts[name] = int(count[0]) if count else 0
    finally:
        con.close()

    return row_counts


def main() -> None:
    settings = get_settings()
    print(f"Ingesting Olist from {settings.olist_raw_dir}")
    print(f"Writing DuckDB to {settings.duckdb_path}")
    counts = ingest_olist(settings=settings)
    width = max(len(name) for name in counts)
    total = 0
    for name, count in sorted(counts.items()):
        print(f"  {name:<{width}}  {count:>10,} rows")
        total += count
    print(f"  {'TOTAL':<{width}}  {total:>10,} rows")
    print("Done.")


if __name__ == "__main__":
    main()
