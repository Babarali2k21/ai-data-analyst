"""Critic node: validate analyst output before finalizing."""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ai_data_analyst.agent.nodes.sql_analyst import preview_query_result
from ai_data_analyst.agent.state import AnalystState, CriticVerdict
from ai_data_analyst.config import Settings

CRITIC_SYSTEM = """\
You are a strict QA critic for an autonomous data analyst.

Pass only if:
- There is no execution/validation error
- The result is relevant to the question
- Findings are grounded in the query result (no invented numbers)
- Empty results are acceptable only if that is a plausible true answer

Fail with concrete, actionable feedback when SQL should be fixed or a different approach is needed.
"""


def make_critic_node(llm: BaseChatModel) -> Any:
    structured = llm.with_structured_output(CriticVerdict)

    def critic(state: AnalystState) -> dict[str, Any]:
        error = (state.get("error") or "").strip()
        findings = (state.get("findings") or "").strip()
        query_result = state.get("query_result") or {}

        # Hard fail on tool errors / empty findings after an error
        if error:
            return {
                "critic_passed": False,
                "critic_feedback": f"Execution/tool error must be fixed: {error}",
                "activity": ["Critic failed (tool error)"],
            }

        if not findings:
            return {
                "critic_passed": False,
                "critic_feedback": "No findings were produced. Produce a valid analysis result.",
                "activity": ["Critic failed (missing findings)"],
            }

        verdict = structured.invoke(
            [
                SystemMessage(content=CRITIC_SYSTEM),
                HumanMessage(
                    content=(
                        f"Question:\n{state['question']}\n\n"
                        f"Plan:\n{state.get('plan')}\n\n"
                        f"SQL:\n{state.get('sql') or '(none)'}\n\n"
                        f"Result:\n{preview_query_result(query_result)}\n\n"
                        f"Findings:\n{findings}\n"
                    )
                ),
            ]
        )
        if not isinstance(verdict, CriticVerdict):
            verdict = CriticVerdict.model_validate(verdict)

        return {
            "critic_passed": verdict.passed,
            "critic_feedback": verdict.feedback,
            "activity": [
                "Critic passed" if verdict.passed else f"Critic failed: {verdict.feedback}"
            ],
        }

    return critic


def route_after_critic(state: AnalystState, settings: Settings) -> Literal["planner", "finalizer"]:
    if state.get("critic_passed"):
        return "finalizer"
    iteration = int(state.get("iteration") or 0)
    if iteration >= settings.max_agent_iterations:
        return "finalizer"
    return "planner"
