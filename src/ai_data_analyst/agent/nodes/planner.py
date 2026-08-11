"""Planner node: create or revise an analysis plan."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ai_data_analyst.agent.state import AnalysisPlan, AnalystState

PLANNER_SYSTEM = """\
You are the planning module of an autonomous data analyst for the Olist e-commerce dataset.

Produce a short plan for answering the user question.
- Prefer tool="sql" for counts, joins, groupings, rankings, simple aggregates, and most analytics.
- Prefer tool="python" when statistical work is clearly required:
  correlation, distribution describe (mean/median/std), percentage change, rolling averages,
  IQR outlier detection, or group mean/median comparisons beyond a simple SQL aggregate.
- The Python analyst will still fetch data via SQL, then run a fixed stats operation
  (no arbitrary code execution).
- If critic recovery_action is switch_to_sql, you MUST set tool="sql".
- If critic recovery_action is switch_to_python, you MUST set tool="python".
- If prior critic feedback exists, revise the plan to address it.
- Keep steps concrete and minimal (2-5).
"""


def make_planner_node(llm: BaseChatModel) -> Any:
    structured = llm.with_structured_output(AnalysisPlan)

    def planner(state: AnalystState) -> dict[str, Any]:
        iteration = int(state.get("iteration") or 0) + 1
        question = state["question"]
        schema_context = state.get("schema_context") or ""
        feedback = state.get("critic_feedback") or ""
        error = state.get("error") or ""
        recovery_action = state.get("recovery_action") or ""
        failure_type = state.get("failure_type") or ""

        user_parts = [
            f"Schema:\n{schema_context}",
            f"\nQuestion:\n{question}",
            f"\nIteration: {iteration}",
        ]
        if recovery_action:
            user_parts.append(f"\nRecovery action required: {recovery_action}")
        if failure_type:
            user_parts.append(f"\nFailure type: {failure_type}")
        if feedback:
            user_parts.append(f"\nCritic feedback to address:\n{feedback}")
        if error:
            user_parts.append(f"\nPrevious error:\n{error}")
        if state.get("sql"):
            user_parts.append(f"\nPrevious SQL:\n{state['sql']}")
        history = state.get("recovery_history") or []
        if history:
            user_parts.append(f"\nRecovery history: {history}")

        plan = structured.invoke(
            [
                SystemMessage(content=PLANNER_SYSTEM),
                HumanMessage(content="\n".join(user_parts)),
            ]
        )
        if not isinstance(plan, AnalysisPlan):
            plan = AnalysisPlan.model_validate(plan)

        # Enforce tool switches from critic recovery
        if recovery_action == "switch_to_sql":
            plan.tool = "sql"
        elif recovery_action == "switch_to_python":
            plan.tool = "python"

        return {
            "plan": plan.model_dump(),
            "iteration": iteration,
            "error": "",
            "critic_passed": False,
            "activity": [f"Planned analysis (iteration {iteration}, tool={plan.tool})"],
        }

    return planner
