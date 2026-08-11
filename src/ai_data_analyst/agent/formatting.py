"""Shared formatting helpers for agent nodes."""

from __future__ import annotations

import json
from typing import Any


def preview_query_result(query_result: dict[str, Any], max_rows: int = 10) -> str:
    if not query_result:
        return "(no result)"
    rows = query_result.get("rows") or []
    payload = {
        "columns": query_result.get("columns"),
        "row_count": query_result.get("row_count"),
        "truncated": query_result.get("truncated"),
        "rows": rows[:max_rows],
    }
    return json.dumps(payload, indent=2, default=str)
