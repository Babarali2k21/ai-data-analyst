"""Shared result preview formatting (SSOT for agent + SQL pipeline)."""

from __future__ import annotations

import json
from typing import Any, Protocol


class _Dumpable(Protocol):
    def model_dump(self) -> dict[str, Any]: ...


def preview_query_result(
    query_result: dict[str, Any] | _Dumpable | None,
    max_rows: int = 10,
) -> str:
    """Format a query result dict or QueryResult for LLM prompts."""
    if query_result is None:
        return "(no result)"
    if isinstance(query_result, dict):
        data = query_result
    else:
        data = query_result.model_dump()
    if not data:
        return "(no result)"
    rows = data.get("rows") or []
    payload = {
        "columns": data.get("columns"),
        "row_count": data.get("row_count"),
        "truncated": data.get("truncated"),
        "rows": rows[:max_rows],
    }
    return json.dumps(payload, indent=2, default=str)
