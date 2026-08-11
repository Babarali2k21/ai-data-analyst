"""FastAPI request/response schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    mode: Literal["agent", "sql"] = "agent"


class AnalysisResponse(BaseModel):
    question: str
    answer: str
    mode: Literal["agent", "sql"]
    sql: str | None = None
    plan: dict[str, Any] = Field(default_factory=dict)
    activity: list[str] = Field(default_factory=list)
    supporting_sql: list[str] = Field(default_factory=list)
    critic_passed: bool | None = None
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


class HealthResponse(BaseModel):
    status: str
    duckdb_ready: bool
    model: str
    dataset: str = "olist"


class DatasetInfoResponse(BaseModel):
    dataset: str
    tables: list[str]
    duckdb_path: str
