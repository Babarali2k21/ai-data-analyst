"""Critic node: validate analyst output and choose recovery actions."""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ai_data_analyst.agent.nodes.sql_analyst import preview_query_result
from ai_data_analyst.agent.recovery import CriticVerdict, recovery_guidance, rule_based_critic
from ai_data_analyst.agent.state import AnalystState
from ai_data_analyst.config import Settings

CRITIC_SYSTEM = """\
You are a strict QA critic for an autonomous data analyst.

Pass only if:
- There is no execution/validation error
- The result is relevant to the question
- Findings are grounded in the query/stats result (no invented numbers)
- Empty results are acceptable only when findings clearly justify emptiness

If failing, set:
- failure_type: irrelevant | hallucination_risk | wrong_tool | incomplete | empty_result
- recovery_action:
  - retry_sql: same SQL approach, fix the query
  - retry_python: same stats approach, fix StatsSpec/data_sql
  - switch_to_sql: Python was wrong tool; use SQL
  - switch_to_python: SQL insufficient; need stats
  - replan: need a different overall approach
  - accept_partial: good enough to finalize despite issues

Be concrete and actionable in feedback.
"""


def make_critic_node(llm: BaseChatModel) -> Any:
    structured = llm.with_structured_output(CriticVerdict)

    def critic(state: AnalystState) -> dict[str, Any]:
        findings = (state.get("findings") or "").strip()
        query_result = state.get("query_result") or {}
        python_result = state.get("python_result") or {}

        rule = rule_based_critic(dict(state))
        if rule.triggered and rule.verdict is not None:
            verdict = rule.verdict
        else:
            verdict_obj = structured.invoke(
                [
                    SystemMessage(content=CRITIC_SYSTEM),
                    HumanMessage(
                        content=(
                            f"Question:\n{state['question']}\n\n"
                            f"Plan:\n{state.get('plan')}\n\n"
                            f"Route:\n{state.get('route')}\n\n"
                            f"SQL:\n{state.get('sql') or '(none)'}\n\n"
                            f"Result:\n{preview_query_result(query_result)}\n\n"
                            f"Python/stats result:\n{python_result or '(none)'}\n\n"
                            f"Findings:\n{findings}\n"
                        )
                    ),
                ]
            )
            verdict = (
                verdict_obj
                if isinstance(verdict_obj, CriticVerdict)
                else CriticVerdict.model_validate(verdict_obj)
            )
            if verdict.passed:
                verdict.failure_type = "none"
                verdict.recovery_action = "accept"

        history_entry = (
            f"{verdict.failure_type}:{verdict.recovery_action}"
            if not verdict.passed
            else "pass:accept"
        )
        activity = (
            ["Critic passed"]
            if verdict.passed
            else [f"Critic failed ({verdict.failure_type} → {verdict.recovery_action})"]
        )
        return {
            "critic_passed": verdict.passed,
            "critic_feedback": recovery_guidance(verdict),
            "failure_type": verdict.failure_type,
            "recovery_action": verdict.recovery_action,
            "recovery_history": [history_entry],
            "activity": activity,
        }

    return critic


def route_after_critic(
    state: AnalystState, settings: Settings
) -> Literal["planner", "sql_analyst", "python_analyst", "visualizer"]:
    """Route to direct retry, replan, or visualization/finalize path."""
    if state.get("critic_passed"):
        return "visualizer"

    iteration = int(state.get("iteration") or 0)
    action = state.get("recovery_action") or "replan"

    if action == "accept_partial" or iteration >= settings.max_agent_iterations:
        return "visualizer"

    # Avoid infinite direct retries: if same action already tried twice, escalate to planner
    history = list(state.get("recovery_history") or [])
    failure = state.get("failure_type") or "tool_error"
    if len(history) >= settings.max_agent_iterations * 2:
        return "visualizer"
    if action in {"retry_sql", "retry_python"} and history.count(f"{failure}:{action}") >= 2:
        return "planner"

    if action == "retry_sql":
        return "sql_analyst"
    if action == "retry_python":
        return "python_analyst"
    if action in {"replan", "switch_to_sql", "switch_to_python"}:
        return "planner"
    return "planner"
