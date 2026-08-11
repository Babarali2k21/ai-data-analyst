"""Python/statistical analyst node: SQL fetch → structured stats → findings."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ai_data_analyst.agent.state import AnalystState
from ai_data_analyst.analyst.sql_pipeline import extract_sql
from ai_data_analyst.config import Settings
from ai_data_analyst.tools.sql import run_sql
from ai_data_analyst.tools.sql_validation import SQLValidationError, validate_sql
from ai_data_analyst.tools.stats import StatsSpec, run_stats

PYTHON_PLAN_SYSTEM = """\
You are the Python/statistics analyst for Olist e-commerce data.

Return a StatsSpec that:
1) Pulls a compact working dataset with read-only DuckDB SQL (data_sql)
2) Chooses one supported operation:
   - describe: mean/median/std/min/max for one numeric column
   - correlation: correlation matrix for 2+ numeric columns
   - pct_change: percentage-change summary for an ordered numeric series
   - rolling_mean: rolling average for an ordered numeric series
   - outliers: IQR outlier detection for one numeric column
   - group_compare: mean/median/std of a value column by a group column

Rules:
- data_sql must be a single SELECT/WITH query.
- Prefer aggregating in SQL when the raw table is huge; otherwise LIMIT appropriately.
- For time series (pct_change/rolling_mean), ORDER BY the time column in SQL.
- columns must match aliases/names returned by data_sql.
- Never request arbitrary Python code — only the structured StatsSpec fields.
"""

PYTHON_FINDINGS_SYSTEM = """\
You are a data analyst. Given the user question, the SQL used to fetch data,
the stats operation, and the stats summary JSON, write a concise factual answer.
Use numbers from the summary. Do not invent values. 1-5 sentences.
"""


def make_python_analyst_node(llm: BaseChatModel, settings: Settings) -> Any:
    structured = llm.with_structured_output(StatsSpec)

    def python_analyst(state: AnalystState) -> dict[str, Any]:
        question = state["question"]
        schema_context = state.get("schema_context") or ""
        feedback = state.get("critic_feedback") or ""
        prior_error = state.get("error") or ""

        try:
            user = (
                f"Schema:\n{schema_context}\n\n"
                f"Question:\n{question}\n\n"
                f"Plan:\n{state.get('plan')}\n"
            )
            if feedback:
                user += f"\nCritic feedback:\n{feedback}\n"
            if prior_error:
                user += f"\nPrevious error:\n{prior_error}\n"

            spec_obj = structured.invoke(
                [
                    SystemMessage(content=PYTHON_PLAN_SYSTEM),
                    HumanMessage(content=user),
                ]
            )
            spec = (
                spec_obj if isinstance(spec_obj, StatsSpec) else StatsSpec.model_validate(spec_obj)
            )
            # Allow models that put fences in data_sql
            spec.data_sql = validate_sql(extract_sql(spec.data_sql))

            query_result = run_sql(
                spec.data_sql,
                settings=settings,
                row_limit=settings.stats_row_limit,
            )
            if not query_result.rows:
                return {
                    "sql": query_result.sql,
                    "query_result": query_result.model_dump(),
                    "python_result": {},
                    "findings": "",
                    "error": "Stats dataset is empty; adjust data_sql",
                    "activity": ["Python analyst fetched empty dataset"],
                }

            df = pd.DataFrame(query_result.rows)
            stats_result = run_stats(df, spec)
            findings = _summarize_stats(
                llm,
                question=question,
                sql=query_result.sql,
                spec=spec,
                summary=stats_result.summary,
            )

            supporting = list(state.get("supporting_sql") or [])
            supporting.append(query_result.sql)
            return {
                "sql": query_result.sql,
                "query_result": query_result.model_dump(),
                "python_result": stats_result.model_dump(),
                "findings": findings,
                "error": "",
                "supporting_sql": supporting,
                "activity": [
                    f"Performed statistical analysis ({spec.operation})",
                ],
            }
        except (SQLValidationError, Exception) as exc:  # noqa: BLE001
            return {
                "sql": state.get("sql") or "",
                "query_result": state.get("query_result") or {},
                "python_result": {},
                "findings": "",
                "error": str(exc),
                "activity": [f"Python analyst error: {exc}"],
            }

    return python_analyst


def _summarize_stats(
    llm: BaseChatModel,
    *,
    question: str,
    sql: str,
    spec: StatsSpec,
    summary: dict[str, Any],
) -> str:
    response = llm.invoke(
        [
            SystemMessage(content=PYTHON_FINDINGS_SYSTEM),
            HumanMessage(
                content=(
                    f"Question:\n{question}\n\n"
                    f"SQL:\n{sql}\n\n"
                    f"Operation: {spec.operation}\n"
                    f"Columns: {spec.columns}\n"
                    f"Group column: {spec.group_column}\n\n"
                    f"Stats summary:\n{json.dumps(summary, indent=2, default=str)}\n"
                )
            ),
        ]
    )
    content = response.content
    return content.strip() if isinstance(content, str) else str(content)
