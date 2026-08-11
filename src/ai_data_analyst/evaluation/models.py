"""Pydantic models for the evaluation harness."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Difficulty = Literal["easy", "medium", "hard"]
ExpectedTool = Literal["sql", "python", "either"]
EvalMode = Literal["sql", "agent"]


class BenchmarkQuestion(BaseModel):
    id: str
    question: str
    difficulty: Difficulty
    category: str
    expected_tool: ExpectedTool = "sql"
    gold_numeric: float | None = None
    numeric_tolerance: float = 0.0
    gold_contains: list[str] = Field(default_factory=list)
    require_judge: bool = False
    notes: str = ""


class BenchmarkSuite(BaseModel):
    name: str
    version: str = "1"
    dataset: str = "olist"
    questions: list[BenchmarkQuestion]


class QuestionResult(BaseModel):
    id: str
    question: str
    difficulty: str
    category: str
    mode: EvalMode
    success: bool
    sql_executed: bool = False
    tool_selected: str | None = None
    tool_correct: bool | None = None
    answer: str = ""
    sql: str | None = None
    numeric_correct: bool | None = None
    contains_correct: bool | None = None
    judge_correct: bool | None = None
    answer_correct: bool | None = None
    hallucinated: bool | None = None
    critic_passed: bool | None = None
    iterations: int = 0
    latency_ms: float = 0.0
    error: str | None = None
    charts: int = 0


class EvalSummary(BaseModel):
    suite: str
    mode: EvalMode
    n_questions: int
    task_completion_rate: float
    sql_execution_accuracy: float
    tool_selection_accuracy: float | None
    answer_accuracy: float | None
    hallucination_rate: float | None
    avg_iterations: float
    avg_latency_ms: float
    results: list[QuestionResult] = Field(default_factory=list)
    extras: dict[str, Any] = Field(default_factory=dict)
