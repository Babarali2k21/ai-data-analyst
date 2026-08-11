"""Router node: choose SQL vs Python analyst from the plan."""

from __future__ import annotations

from typing import Any, Literal

from ai_data_analyst.agent.state import AnalystState


def router(state: AnalystState) -> dict[str, Any]:
    plan = state.get("plan") or {}
    tool = plan.get("tool", "sql")
    route: Literal["sql", "python"] = "python" if tool == "python" else "sql"
    return {
        "route": route,
        "activity": [f"Routed to {route} analyst"],
    }


def route_after_planner(state: AnalystState) -> Literal["sql_analyst", "python_analyst"]:
    route = state.get("route") or "sql"
    if route == "python":
        return "python_analyst"
    return "sql_analyst"
