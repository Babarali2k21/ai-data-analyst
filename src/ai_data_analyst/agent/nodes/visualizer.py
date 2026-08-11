"""Visualizer node: produce structured ChartSpec(s) for the UI."""

from __future__ import annotations

import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ai_data_analyst.agent.state import AnalystState
from ai_data_analyst.config import Settings
from ai_data_analyst.tools.chart_render import render_chart_png
from ai_data_analyst.tools.charts import (
    ChartProposal,
    ChartSpec,
    attach_series,
    chart_from_group_compare,
    heuristic_chart_from_rows,
    validate_chart_against_columns,
)

VISUALIZER_SYSTEM = """\
You propose ONE chart for an analytics UI. Do NOT write frontend code.
Return a ChartProposal over columns that exist in the result.
Prefer:
- line for time series
- bar for categories / rankings / group comparisons
- scatter for two numeric measures
- hist for a single numeric distribution
Set should_chart=false for a single scalar answer (e.g. one count) with no useful series.
"""


def make_visualizer_node(llm: BaseChatModel, settings: Settings) -> Any:
    structured = llm.with_structured_output(ChartProposal)

    def visualizer(state: AnalystState) -> dict[str, Any]:
        query_result = state.get("query_result") or {}
        python_result = state.get("python_result") or {}
        rows = list(query_result.get("rows") or [])
        columns = list(query_result.get("columns") or (list(rows[0].keys()) if rows else []))
        charts: list[dict[str, Any]] = []
        chart_paths: list[str] = []

        # Stats group_compare → bar chart of group means
        if python_result.get("operation") == "group_compare":
            group_chart = chart_from_group_compare(python_result.get("summary") or {})
            if group_chart is not None:
                charts.append(group_chart.model_dump())

        # Tabular query result → LLM proposal with heuristic fallback
        if rows and columns and not _is_single_scalar(rows, columns):
            proposal = _propose_chart(
                structured,
                question=state.get("question") or "",
                findings=state.get("findings") or "",
                columns=columns,
                sample_rows=rows[:8],
            )
            spec = validate_chart_against_columns(proposal, columns)
            if spec is None:
                spec = heuristic_chart_from_rows(rows, title=_title_from_question(state))
            if spec is not None:
                spec = attach_series(spec, rows)
                charts.append(spec.model_dump())

        # Deduplicate by title+type+x+y
        charts = _dedupe_charts(charts)

        # Optional PNG render for demos
        for index, chart_dict in enumerate(charts):
            try:
                spec = ChartSpec.model_validate(chart_dict)
                if not spec.series:
                    continue
                safe = _slug(spec.title) or f"chart_{index}"
                path = settings.charts_dir / f"{safe}.png"
                render_chart_png(spec, path)
                chart_paths.append(str(path))
                chart_dict["image_path"] = str(path)
            except Exception:  # noqa: BLE001 — rendering is best-effort
                continue

        activity = (
            [f"Generated visualization ({len(charts)} chart(s))"]
            if charts
            else ["Skipped visualization (no chartable series)"]
        )
        return {
            "charts": charts,
            "chart_paths": chart_paths,
            "activity": activity,
        }

    return visualizer


def _propose_chart(
    structured: Any,
    *,
    question: str,
    findings: str,
    columns: list[str],
    sample_rows: list[dict[str, Any]],
) -> ChartProposal:
    try:
        result = structured.invoke(
            [
                SystemMessage(content=VISUALIZER_SYSTEM),
                HumanMessage(
                    content=(
                        f"Question:\n{question}\n\n"
                        f"Findings:\n{findings}\n\n"
                        f"Columns: {columns}\n"
                        f"Sample rows: {sample_rows}\n"
                    )
                ),
            ]
        )
        if isinstance(result, ChartProposal):
            return result
        return ChartProposal.model_validate(result)
    except Exception:  # noqa: BLE001
        return ChartProposal(should_chart=True, type="bar", x="", y=None, title="")


def _is_single_scalar(rows: list[dict[str, Any]], columns: list[str]) -> bool:
    return len(rows) == 1 and len(columns) == 1


def _title_from_question(state: AnalystState) -> str | None:
    question = (state.get("question") or "").strip()
    return question[:80] if question else None


def _dedupe_charts(charts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []
    for chart in charts:
        key = (chart.get("type"), chart.get("x"), chart.get("y"), chart.get("title"))
        if key in seen:
            continue
        seen.add(key)
        out.append(chart)
    return out


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return slug[:60]
