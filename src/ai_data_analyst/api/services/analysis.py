"""Analysis application service (mode dispatch, timeout, DTO mapping)."""

from __future__ import annotations

import contextvars
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from typing import Literal

from ai_data_analyst.agent.graph import AgentResult, run_analyst_agent
from ai_data_analyst.analyst.sql_pipeline import SQLAnalystResult, ask_sql
from ai_data_analyst.api.schemas import AnalysisResponse, ObservabilityInfo
from ai_data_analyst.config import Settings
from ai_data_analyst.observability.context import get_request_id, start_run_metrics
from ai_data_analyst.observability.logging import get_logger

logger = get_logger("ai_data_analyst.analysis")


class AnalysisNotReadyError(Exception):
    """Service cannot run (missing key or database)."""

    def __init__(self, message: str, *, status_code: int = 503) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AnalysisTimeoutError(Exception):
    def __init__(self, timeout_seconds: float) -> None:
        message = f"Analysis timed out after {timeout_seconds:.0f}s"
        super().__init__(message)
        self.message = message
        self.status_code = 504


def _ensure_ready(settings: Settings) -> None:
    if not settings.openai_api_key:
        raise AnalysisNotReadyError("OPENAI_API_KEY is not configured")
    if not settings.duckdb_ready:
        raise AnalysisNotReadyError(
            "DuckDB analytics database is missing. Run: make ingest"
        )


def _to_response(
    result: SQLAnalystResult | AgentResult,
    *,
    mode: Literal["sql", "agent"],
    observability: ObservabilityInfo,
) -> AnalysisResponse:
    if isinstance(result, SQLAnalystResult):
        return AnalysisResponse(
            question=result.question,
            answer=result.answer,
            mode="sql",
            sql=result.sql,
            activity=["Ran Phase 2 SQL analyst"],
            supporting_sql=[result.sql],
            iteration=result.attempts,
            model=result.model,
            query_result=result.query_result.model_dump(),
            observability=observability,
        )
    payload = result.model_dump()
    return AnalysisResponse(mode="agent", observability=observability, **payload)


def run_analysis(
    question: str,
    *,
    mode: Literal["sql", "agent"],
    settings: Settings,
) -> AnalysisResponse:
    """Run SQL or agent analysis with timeout and observability."""
    _ensure_ready(settings)
    metrics = start_run_metrics(request_id=get_request_id())
    ctx = contextvars.copy_context()

    logger.info(
        "analysis_started",
        extra={"event": "analysis_started", "mode": mode, "path": "/api/v1/analysis"},
    )

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            try:
                if mode == "sql":

                    def _run_sql() -> SQLAnalystResult:
                        return ask_sql(question, settings=settings)

                    result: SQLAnalystResult | AgentResult = pool.submit(
                        ctx.run, _run_sql
                    ).result(timeout=settings.api_analysis_timeout_seconds)
                else:

                    def _run_agent() -> AgentResult:
                        return run_analyst_agent(question, settings=settings)

                    result = pool.submit(ctx.run, _run_agent).result(
                        timeout=settings.api_analysis_timeout_seconds
                    )
            except FuturesTimeout as exc:
                raise AnalysisTimeoutError(settings.api_analysis_timeout_seconds) from exc

        obs = ObservabilityInfo(**metrics.as_dict())
        response = _to_response(result, mode=mode, observability=obs)
        logger.info(
            "analysis_completed",
            extra={
                "event": "analysis_completed",
                "status_code": 200,
                "latency_ms": obs.total_latency_ms,
                "path": "/api/v1/analysis",
            },
        )
        return response
    except (AnalysisNotReadyError, AnalysisTimeoutError):
        raise
    except Exception:
        logger.exception(
            "analysis_failed",
            extra={"event": "analysis_failed", "path": "/api/v1/analysis"},
        )
        raise
