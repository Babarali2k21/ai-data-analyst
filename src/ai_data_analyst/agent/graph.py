"""Compile and run the LangGraph analyst agent."""

from __future__ import annotations

import argparse
from functools import partial
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from ai_data_analyst.agent.nodes.critic import make_critic_node, route_after_critic
from ai_data_analyst.agent.nodes.finalizer import make_finalizer_node
from ai_data_analyst.agent.nodes.planner import make_planner_node
from ai_data_analyst.agent.nodes.python_analyst import make_python_analyst_node
from ai_data_analyst.agent.nodes.router import route_after_planner, router
from ai_data_analyst.agent.nodes.sql_analyst import make_sql_analyst_node
from ai_data_analyst.agent.nodes.visualizer import make_visualizer_node
from ai_data_analyst.agent.state import AnalystState
from ai_data_analyst.analyst.context import build_schema_context
from ai_data_analyst.config import Settings, get_settings
from ai_data_analyst.llm.client import get_chat_model


class AgentResult(BaseModel):
    question: str
    answer: str
    sql: str | None = None
    plan: dict[str, Any] = Field(default_factory=dict)
    activity: list[str] = Field(default_factory=list)
    supporting_sql: list[str] = Field(default_factory=list)
    critic_passed: bool = False
    critic_feedback: str = ""
    failure_type: str = "none"
    recovery_action: str = "accept"
    recovery_history: list[str] = Field(default_factory=list)
    iteration: int = 0
    model: str = ""
    query_result: dict[str, Any] = Field(default_factory=dict)
    python_result: dict[str, Any] = Field(default_factory=dict)
    charts: list[dict[str, Any]] = Field(default_factory=list)
    chart_paths: list[str] = Field(default_factory=list)


def build_analyst_graph(
    *,
    llm: BaseChatModel | None = None,
    settings: Settings | None = None,
) -> Any:
    """Build planner → router → analysts → critic → visualizer → finalizer."""
    settings = settings or get_settings()
    llm = llm or get_chat_model(settings)

    graph = StateGraph(AnalystState)
    graph.add_node("planner", make_planner_node(llm))
    graph.add_node("router", router)
    graph.add_node("sql_analyst", make_sql_analyst_node(llm, settings))
    graph.add_node("python_analyst", make_python_analyst_node(llm, settings))
    graph.add_node("critic", make_critic_node(llm))
    graph.add_node("visualizer", make_visualizer_node(llm, settings))
    graph.add_node("finalizer", make_finalizer_node(llm))

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "router")
    graph.add_conditional_edges(
        "router",
        route_after_planner,
        {
            "sql_analyst": "sql_analyst",
            "python_analyst": "python_analyst",
        },
    )
    graph.add_edge("sql_analyst", "critic")
    graph.add_edge("python_analyst", "critic")
    graph.add_conditional_edges(
        "critic",
        partial(route_after_critic, settings=settings),
        {
            "planner": "planner",
            "sql_analyst": "sql_analyst",
            "python_analyst": "python_analyst",
            "visualizer": "visualizer",
        },
    )
    graph.add_edge("visualizer", "finalizer")
    graph.add_edge("finalizer", END)
    return graph.compile()


def run_analyst_agent(
    question: str,
    *,
    llm: BaseChatModel | None = None,
    settings: Settings | None = None,
) -> AgentResult:
    """Run the LangGraph analyst end-to-end."""
    settings = settings or get_settings()
    llm = llm or get_chat_model(settings)
    app = build_analyst_graph(llm=llm, settings=settings)

    initial: AnalystState = {
        "question": question,
        "schema_context": build_schema_context(settings),
        "supporting_sql": [],
        "activity": ["Inspected dataset schema"],
        "iteration": 0,
        "model": settings.llm_model,
        "critic_passed": False,
        "critic_feedback": "",
        "failure_type": "none",
        "recovery_action": "accept",
        "recovery_history": [],
        "error": "",
        "findings": "",
        "answer": "",
        "sql": "",
        "query_result": {},
        "python_result": {},
        "charts": [],
        "chart_paths": [],
        "plan": {},
    }
    final_state = app.invoke(initial)

    return AgentResult(
        question=question,
        answer=str(final_state.get("answer") or ""),
        sql=final_state.get("sql") or None,
        plan=dict(final_state.get("plan") or {}),
        activity=list(final_state.get("activity") or []),
        supporting_sql=list(final_state.get("supporting_sql") or []),
        critic_passed=bool(final_state.get("critic_passed")),
        critic_feedback=str(final_state.get("critic_feedback") or ""),
        failure_type=str(final_state.get("failure_type") or "none"),
        recovery_action=str(final_state.get("recovery_action") or "accept"),
        recovery_history=list(final_state.get("recovery_history") or []),
        iteration=int(final_state.get("iteration") or 0),
        model=settings.llm_model,
        query_result=dict(final_state.get("query_result") or {}),
        python_result=dict(final_state.get("python_result") or {}),
        charts=list(final_state.get("charts") or []),
        chart_paths=list(final_state.get("chart_paths") or []),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="LangGraph analyst agent")
    parser.add_argument("question", nargs="+", help="Natural language analytics question")
    parser.add_argument("--json", action="store_true", help="Print full JSON result")
    args = parser.parse_args()
    question = " ".join(args.question)

    result = run_analyst_agent(question)
    if args.json:
        print(result.model_dump_json(indent=2))
        return

    print(f"Model: {result.model}")
    print(f"Iterations: {result.iteration}")
    print(f"Critic: {'PASS' if result.critic_passed else 'FAIL'}")
    if not result.critic_passed:
        print(f"Failure: {result.failure_type} → {result.recovery_action}")
    if result.recovery_history:
        print(f"Recovery history: {result.recovery_history}")
    if result.plan:
        print(f"\nPlan goal: {result.plan.get('goal')}")
        print(f"Tool: {result.plan.get('tool')}")
    print("\nActivity:")
    for step in result.activity:
        print(f"  - {step}")
    if result.sql:
        print("\nSQL:")
        print(result.sql)
    if result.python_result:
        print(f"\nStats operation: {result.python_result.get('operation')}")
        print(f"Stats summary: {result.python_result.get('summary')}")
    if result.charts:
        print("\nCharts:")
        for chart in result.charts:
            print(
                f"  - type={chart.get('type')} x={chart.get('x')} "
                f"y={chart.get('y')} title={chart.get('title')!r}"
            )
            if chart.get("image_path"):
                print(f"    image: {chart['image_path']}")
    print("\nAnswer:")
    print(result.answer)


if __name__ == "__main__":
    main()
