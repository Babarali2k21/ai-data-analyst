"""Request/run context for observability."""

from __future__ import annotations

import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_run_id: ContextVar[str | None] = ContextVar("run_id", default=None)


def new_id(prefix: str = "") -> str:
    value = uuid.uuid4().hex[:12]
    return f"{prefix}{value}" if prefix else value


def set_request_id(request_id: str | None = None) -> str:
    value = request_id or new_id("req_")
    _request_id.set(value)
    return value


def get_request_id() -> str | None:
    return _request_id.get()


def set_run_id(run_id: str | None = None) -> str:
    value = run_id or new_id("run_")
    _run_id.set(value)
    return value


def get_run_id() -> str | None:
    return _run_id.get()


@dataclass
class RunMetrics:
    """Timing and usage counters for one analysis run."""

    run_id: str
    request_id: str | None = None
    started_at: float = field(default_factory=time.perf_counter)
    llm_calls: int = 0
    llm_latency_ms: float = 0.0
    sql_calls: int = 0
    sql_latency_ms: float = 0.0
    tool_errors: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    extras: dict[str, Any] = field(default_factory=dict)

    def mark_llm(
        self,
        latency_ms: float,
        *,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        self.llm_calls += 1
        self.llm_latency_ms += latency_ms
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens

    def mark_sql(self, latency_ms: float, *, error: bool = False) -> None:
        self.sql_calls += 1
        self.sql_latency_ms += latency_ms
        if error:
            self.tool_errors += 1

    @property
    def total_latency_ms(self) -> float:
        return (time.perf_counter() - self.started_at) * 1000

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def estimate_cost_usd(
        self,
        *,
        input_per_mtok: float = 0.40,
        output_per_mtok: float = 1.60,
    ) -> float:
        """Rough gpt-4.1-mini style estimate (USD)."""
        return (self.prompt_tokens / 1_000_000) * input_per_mtok + (
            self.completion_tokens / 1_000_000
        ) * output_per_mtok

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "request_id": self.request_id,
            "total_latency_ms": round(self.total_latency_ms, 2),
            "llm_calls": self.llm_calls,
            "llm_latency_ms": round(self.llm_latency_ms, 2),
            "sql_calls": self.sql_calls,
            "sql_latency_ms": round(self.sql_latency_ms, 2),
            "tool_errors": self.tool_errors,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.estimate_cost_usd(), 6),
            **self.extras,
        }


_metrics: ContextVar[RunMetrics | None] = ContextVar("run_metrics", default=None)


def start_run_metrics(*, run_id: str | None = None, request_id: str | None = None) -> RunMetrics:
    metrics = RunMetrics(run_id=run_id or set_run_id(), request_id=request_id or get_request_id())
    set_run_id(metrics.run_id)
    _metrics.set(metrics)
    return metrics


def get_run_metrics() -> RunMetrics | None:
    return _metrics.get()
