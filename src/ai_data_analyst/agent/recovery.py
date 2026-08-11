"""Rule-based critic checks and recovery taxonomy."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel

FailureType = Literal[
    "none",
    "tool_error",
    "empty_result",
    "missing_findings",
    "schema_mismatch",
    "irrelevant",
    "hallucination_risk",
    "wrong_tool",
    "incomplete",
]

RecoveryAction = Literal[
    "accept",
    "retry_sql",
    "retry_python",
    "switch_to_sql",
    "switch_to_python",
    "replan",
    "accept_partial",
]


class CriticVerdict(BaseModel):
    """Critic pass/fail decision with recovery guidance."""

    passed: bool
    feedback: str
    failure_type: FailureType = "none"
    recovery_action: RecoveryAction = "accept"


class RuleCheckResult(BaseModel):
    """Deterministic pre-LLM critic result (None means continue to LLM critic)."""

    triggered: bool = False
    verdict: CriticVerdict | None = None


_SCHEMA_ERROR = re.compile(
    r"(catalog error|binder error|column .+ not found|table .+ does not exist|"
    r"referenced column|unknown column|missing columns)",
    re.IGNORECASE,
)
_SYNTAX_ERROR = re.compile(r"(parser error|syntax error)", re.IGNORECASE)


def classify_tool_error(error: str, route: str) -> CriticVerdict:
    """Map a tool exception string to failure type + recovery action."""
    if _SCHEMA_ERROR.search(error):
        return CriticVerdict(
            passed=False,
            failure_type="schema_mismatch",
            recovery_action="retry_sql" if route != "python" else "retry_python",
            feedback=(
                "Schema/catalog mismatch. Fix table/column names to match the provided "
                f"schema. Error: {error}"
            ),
        )
    if _SYNTAX_ERROR.search(error):
        return CriticVerdict(
            passed=False,
            failure_type="tool_error",
            recovery_action="retry_sql" if route != "python" else "retry_python",
            feedback=f"SQL/syntax error. Rewrite a valid DuckDB SELECT/WITH. Error: {error}",
        )

    # Generic tool failure: retry same tool once, else planner can switch later
    action: RecoveryAction = "retry_python" if route == "python" else "retry_sql"
    return CriticVerdict(
        passed=False,
        failure_type="tool_error",
        recovery_action=action,
        feedback=f"Execution/tool error must be fixed: {error}",
    )


def rule_based_critic(state: dict[str, Any]) -> RuleCheckResult:
    """Apply cheap deterministic checks before calling the LLM critic."""
    error = (state.get("error") or "").strip()
    findings = (state.get("findings") or "").strip()
    route = state.get("route") or (state.get("plan") or {}).get("tool") or "sql"
    query_result = state.get("query_result") or {}
    python_result = state.get("python_result") or {}

    if error:
        return RuleCheckResult(triggered=True, verdict=classify_tool_error(error, str(route)))

    if not findings:
        return RuleCheckResult(
            triggered=True,
            verdict=CriticVerdict(
                passed=False,
                failure_type="missing_findings",
                recovery_action="replan",
                feedback="No findings were produced. Produce a valid analysis result.",
            ),
        )

    row_count = query_result.get("row_count")
    rows = query_result.get("rows") or []
    # Empty dataset after a successful query — often wrong filters; ask for repair
    if row_count == 0 or (isinstance(rows, list) and len(rows) == 0 and not python_result):
        # Allow empty if findings explicitly say so is handled by LLM critic; here we flag
        # only when findings look non-explanatory/short placeholders
        if len(findings) < 40:
            return RuleCheckResult(
                triggered=True,
                verdict=CriticVerdict(
                    passed=False,
                    failure_type="empty_result",
                    recovery_action="retry_sql" if route != "python" else "retry_python",
                    feedback=(
                        "Query returned no rows and findings are insufficient. "
                        "Relax filters or fix joins/aggregations."
                    ),
                ),
            )

    return RuleCheckResult(triggered=False, verdict=None)


def recovery_guidance(verdict: CriticVerdict) -> str:
    """Human-readable recovery instructions for planner / analysts."""
    mapping = {
        "accept": "No recovery needed.",
        "retry_sql": "Retry the SQL analyst with a corrected query; keep the same goal.",
        "retry_python": "Retry the Python/stats analyst with a corrected StatsSpec/data_sql.",
        "switch_to_sql": "Switch tool to sql and answer with DuckDB aggregation/joins.",
        "switch_to_python": "Switch tool to python for statistical analysis on a fetched dataset.",
        "replan": "Create a new plan; previous approach was insufficient.",
        "accept_partial": "Finalize with the best partial answer available.",
    }
    action = mapping.get(verdict.recovery_action, "Replan.")
    return (
        f"failure_type={verdict.failure_type}; recovery_action={verdict.recovery_action}. "
        f"{action} Feedback: {verdict.feedback}"
    )
