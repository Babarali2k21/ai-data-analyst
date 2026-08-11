"""LangGraph analyst agent state and shared models."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from pydantic import BaseModel, Field

from ai_data_analyst.agent.recovery import CriticVerdict, FailureType, RecoveryAction

__all__ = [
    "AnalysisPlan",
    "AnalystState",
    "CriticVerdict",
    "FailureType",
    "RecoveryAction",
]


class AnalysisPlan(BaseModel):
    """Planner output: what to do and which tool to use."""

    goal: str
    steps: list[str] = Field(default_factory=list)
    tool: Literal["sql", "python"] = "sql"
    rationale: str = ""


class AnalystState(TypedDict, total=False):
    """Shared state flowing through the LangGraph agent."""

    question: str
    schema_context: str
    plan: dict[str, Any]
    route: Literal["sql", "python"]
    sql: str
    query_result: dict[str, Any]
    python_result: dict[str, Any]
    findings: str
    critic_passed: bool
    critic_feedback: str
    failure_type: str
    recovery_action: str
    recovery_history: Annotated[list[str], operator.add]
    answer: str
    supporting_sql: list[str]
    activity: Annotated[list[str], operator.add]
    iteration: int
    error: str
    model: str
