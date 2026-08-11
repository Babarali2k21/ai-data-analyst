"""Structured chart specifications (no arbitrary frontend code)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ChartType = Literal["line", "bar", "scatter", "hist"]


class ChartSpec(BaseModel):
    """Frontend-ready chart contract returned by the agent."""

    type: ChartType
    x: str
    y: str | None = None
    title: str
    series: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Optional truncated data points for rendering",
    )


class ChartProposal(BaseModel):
    """LLM proposal for a chart over an existing result set."""

    should_chart: bool = True
    type: ChartType = "bar"
    x: str = ""
    y: str | None = None
    title: str = ""
    reason: str = ""


def validate_chart_against_columns(
    proposal: ChartProposal,
    columns: list[str],
) -> ChartSpec | None:
    """Accept a proposal only when x/y exist in the result columns."""
    if not proposal.should_chart:
        return None
    if not proposal.x or proposal.x not in columns:
        return None
    if proposal.type != "hist":
        if not proposal.y or proposal.y not in columns:
            return None
        if proposal.x == proposal.y:
            return None
    title = proposal.title.strip() or _default_title(proposal.type, proposal.x, proposal.y)
    return ChartSpec(type=proposal.type, x=proposal.x, y=proposal.y, title=title)


def heuristic_chart_from_rows(
    rows: list[dict[str, Any]],
    *,
    title: str | None = None,
) -> ChartSpec | None:
    """Build a simple chart when the LLM skips or fails validation."""
    if not rows:
        return None
    columns = list(rows[0].keys())
    if len(columns) < 1:
        return None

    # Single numeric column → histogram
    if len(columns) == 1:
        col = columns[0]
        if _is_number(rows[0].get(col)):
            return ChartSpec(
                type="hist",
                x=col,
                y=None,
                title=title or f"Distribution of {col}",
                series=_series(rows, col, None),
            )
        return None

    x_col = columns[0]
    # Prefer a numeric y
    y_col = next((c for c in columns[1:] if _is_number(rows[0].get(c))), None)
    if y_col is None:
        return None

    chart_type: ChartType = "line" if _looks_temporal(x_col) else "bar"
    if _is_number(rows[0].get(x_col)) and _is_number(rows[0].get(y_col)):
        chart_type = "scatter"

    return ChartSpec(
        type=chart_type,
        x=x_col,
        y=y_col,
        title=title or _default_title(chart_type, x_col, y_col),
        series=_series(rows, x_col, y_col),
    )


def chart_from_group_compare(summary: dict[str, Any]) -> ChartSpec | None:
    groups = summary.get("groups") or []
    if not groups:
        return None
    value_col = str(summary.get("value_column") or "mean")
    rows = [{"group": g.get("group"), "mean": g.get("mean")} for g in groups]
    return ChartSpec(
        type="bar",
        x="group",
        y="mean",
        title=f"Mean {value_col} by {summary.get('group_column', 'group')}",
        series=rows,
    )


def attach_series(spec: ChartSpec, rows: list[dict[str, Any]], max_points: int = 100) -> ChartSpec:
    """Copy x/y values from rows into the chart series payload."""
    series = _series(rows, spec.x, spec.y, max_points=max_points)
    return spec.model_copy(update={"series": series})


def _series(
    rows: list[dict[str, Any]],
    x: str,
    y: str | None,
    max_points: int = 100,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows[:max_points]:
        point: dict[str, Any] = {"x": row.get(x)}
        if y is not None:
            point["y"] = row.get(y)
        else:
            point["y"] = row.get(x)
        out.append(point)
    return out


def _default_title(chart_type: str, x: str, y: str | None) -> str:
    if chart_type == "hist" or y is None:
        return f"Distribution of {x}"
    return f"{y} by {x}"


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _looks_temporal(name: str) -> bool:
    lower = name.lower()
    return any(token in lower for token in ("date", "month", "year", "week", "time", "day"))
