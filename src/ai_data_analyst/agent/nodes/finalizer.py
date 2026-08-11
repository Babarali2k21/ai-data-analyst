"""Finalizer node: produce the user-facing answer."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ai_data_analyst.agent.nodes.sql_analyst import preview_query_result
from ai_data_analyst.agent.state import AnalystState

FINALIZER_SYSTEM = """\
You are the final responder for an autonomous data analyst.
Write a clear answer to the user question using the findings and query result.
If the critic did not pass and iterations were exhausted, explain the limitation briefly
and give the best partial answer available. Do not invent numbers.
"""


def make_finalizer_node(llm: BaseChatModel) -> Any:
    def finalizer(state: AnalystState) -> dict[str, Any]:
        findings = (state.get("findings") or "").strip()
        passed = bool(state.get("critic_passed"))
        feedback = state.get("critic_feedback") or ""
        query_result = state.get("query_result") or {}

        if passed and findings:
            answer = findings
            return {
                "answer": answer,
                "activity": ["Finalized answer"],
            }

        response = llm.invoke(
            [
                SystemMessage(content=FINALIZER_SYSTEM),
                HumanMessage(
                    content=(
                        f"Question:\n{state['question']}\n\n"
                        f"Critic passed: {passed}\n"
                        f"Critic feedback: {feedback or '(none)'}\n"
                        f"Error: {state.get('error') or '(none)'}\n"
                        f"SQL:\n{state.get('sql') or '(none)'}\n\n"
                        f"Result:\n{preview_query_result(query_result)}\n\n"
                        f"Findings:\n{findings or '(none)'}\n"
                    )
                ),
            ]
        )
        content = response.content
        answer = content.strip() if isinstance(content, str) else str(content)
        activity_msg = (
                "Finalized answer (with limitations)" if not passed else "Finalized answer"
            )
        return {
            "answer": answer,
            "activity": [activity_msg],
        }

    return finalizer
