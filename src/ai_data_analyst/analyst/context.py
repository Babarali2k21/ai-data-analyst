"""Build schema context strings for the SQL analyst."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_data_analyst.config import Settings, get_settings
from ai_data_analyst.data.ingestion.olist import load_metadata, load_schema


def _load_profile(metadata_dir: Path) -> dict[str, Any] | None:
    path = metadata_dir / "profile.json"
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else None


def build_schema_context(settings: Settings | None = None) -> str:
    """Compact schema + relationships + row counts for the LLM prompt."""
    settings = settings or get_settings()
    metadata = load_metadata(settings.olist_metadata_dir)
    schema = load_schema(settings.olist_metadata_dir)
    profile = _load_profile(settings.olist_metadata_dir)

    lines: list[str] = []
    dataset = metadata.get("dataset", {})
    lines.append(f"Dataset: {dataset.get('name', 'olist')} ({dataset.get('id', 'olist')})")
    if dataset.get("description"):
        lines.append(str(dataset["description"]))
    lines.append("")
    lines.append("Tables:")

    for table in metadata.get("tables", []):
        name = table["name"]
        desc = table.get("description", "")
        pk = table.get("primary_key", [])
        row_count = None
        if profile and "tables" in profile:
            row_count = profile["tables"].get(name, {}).get("row_count")
        header = f"- {name}"
        if row_count is not None:
            header += f" ({row_count:,} rows)"
        if desc:
            header += f": {desc}"
        lines.append(header)
        if pk:
            lines.append(f"  primary_key: {', '.join(pk)}")
        columns = schema.get(name, {}).get("columns", [])
        col_parts = [f"{c['name']} {c['type']}" for c in columns]
        lines.append("  columns: " + ", ".join(col_parts))

    relationships = metadata.get("relationships", [])
    if relationships:
        lines.append("")
        lines.append("Relationships:")
        for rel in relationships:
            lines.append(f"- {rel['from']} -> {rel['to']}")

    lines.append("")
    lines.append("Notes:")
    lines.append("- Use DuckDB SQL dialect.")
    lines.append("- Prefer joins via documented relationships.")
    lines.append("- Revenue/price usually comes from order_items.price (not payments alone).")
    lines.append("- Timestamps for order timing: orders.order_purchase_timestamp.")
    return "\n".join(lines)
