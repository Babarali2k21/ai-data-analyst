"""Analysis API routes."""

from __future__ import annotations

import contextvars
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from ai_data_analyst.agent.graph import AgentResult, run_analyst_agent
from ai_data_analyst.analyst.sql_pipeline import SQLAnalystResult, ask_sql
from ai_data_analyst.api.deps import get_rate_limiter, settings_dep
from ai_data_analyst.api.schemas import AnalysisRequest, AnalysisResponse, ObservabilityInfo
from ai_data_analyst.config import Settings
from ai_data_analyst.observability.context import get_request_id, start_run_metrics
from ai_data_analyst.observability.logging import get_logger
from ai_data_analyst.security.auth import require_api_key
from ai_data_analyst.security.rate_limit import client_key

router = APIRouter(prefix="/api/v1", tags=["analysis"])
SettingsDep = Annotated[Settings, Depends(settings_dep)]
logger = get_logger("ai_data_analyst.analysis")


@router.post("/analysis", response_model=AnalysisResponse)
def create_analysis(
    body: AnalysisRequest,
    request: Request,
    settings: SettingsDep,
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> AnalysisResponse:
    """Run the SQL pipeline or full LangGraph analyst agent."""
    presented_key = require_api_key(
        settings, authorization=authorization, x_api_key=x_api_key
    )
    get_rate_limiter().check(client_key(request, presented_key))

    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured")
    if not settings.duckdb_path.exists() or settings.duckdb_path.stat().st_size == 0:
        raise HTTPException(
            status_code=503,
            detail="DuckDB analytics database is missing. Run: make ingest",
        )

    metrics = start_run_metrics(request_id=get_request_id())
    # Propagate request/run ContextVars into the worker thread used for timeouts.
    ctx = contextvars.copy_context()
    logger.info(
        "analysis_started",
        extra={
            "event": "analysis_started",
            "mode": body.mode,
            "path": "/api/v1/analysis",
        },
    )

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            try:
                if body.mode == "sql":

                    def _run_sql() -> SQLAnalystResult:
                        return ask_sql(body.question, settings=settings)

                    result: SQLAnalystResult | AgentResult = pool.submit(
                        ctx.run, _run_sql
                    ).result(timeout=settings.api_analysis_timeout_seconds)
                else:

                    def _run_agent() -> AgentResult:
                        return run_analyst_agent(body.question, settings=settings)

                    result = pool.submit(ctx.run, _run_agent).result(
                        timeout=settings.api_analysis_timeout_seconds
                    )
            except FuturesTimeout as exc:
                raise HTTPException(
                    status_code=504,
                    detail=(
                        "Analysis timed out after "
                        f"{settings.api_analysis_timeout_seconds:.0f}s"
                    ),
                ) from exc

        obs = ObservabilityInfo(**metrics.as_dict())
        if isinstance(result, SQLAnalystResult):
            response = AnalysisResponse(
                question=result.question,
                answer=result.answer,
                mode="sql",
                sql=result.sql,
                activity=["Ran Phase 2 SQL analyst"],
                supporting_sql=[result.sql],
                iteration=result.attempts,
                model=result.model,
                query_result=result.query_result.model_dump(),
                observability=obs,
            )
        else:
            response = AnalysisResponse(
                question=result.question,
                answer=result.answer,
                mode="agent",
                sql=result.sql,
                plan=result.plan,
                activity=result.activity,
                supporting_sql=result.supporting_sql,
                critic_passed=result.critic_passed,
                critic_feedback=result.critic_feedback,
                failure_type=result.failure_type,
                recovery_action=result.recovery_action,
                recovery_history=result.recovery_history,
                iteration=result.iteration,
                model=result.model,
                query_result=result.query_result,
                python_result=result.python_result,
                charts=result.charts,
                chart_paths=result.chart_paths,
                observability=obs,
            )

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
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "analysis_failed",
            extra={
                "event": "analysis_failed",
                "error": str(exc),
                "path": "/api/v1/analysis",
            },
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc
