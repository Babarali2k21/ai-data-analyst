"""Analysis API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ai_data_analyst.agent.graph import run_analyst_agent
from ai_data_analyst.analyst.sql_pipeline import ask_sql
from ai_data_analyst.api.deps import settings_dep
from ai_data_analyst.api.schemas import AnalysisRequest, AnalysisResponse
from ai_data_analyst.config import Settings

router = APIRouter(prefix="/api/v1", tags=["analysis"])
SettingsDep = Annotated[Settings, Depends(settings_dep)]


@router.post("/analysis", response_model=AnalysisResponse)
def create_analysis(body: AnalysisRequest, settings: SettingsDep) -> AnalysisResponse:
    """Run the SQL pipeline or full LangGraph analyst agent."""
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured")
    if not settings.duckdb_path.exists() or settings.duckdb_path.stat().st_size == 0:
        raise HTTPException(
            status_code=503,
            detail="DuckDB analytics database is missing. Run: make ingest",
        )

    try:
        if body.mode == "sql":
            result = ask_sql(body.question, settings=settings)
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
            )

        agent = run_analyst_agent(body.question, settings=settings)
        return AnalysisResponse(
            question=agent.question,
            answer=agent.answer,
            mode="agent",
            sql=agent.sql,
            plan=agent.plan,
            activity=agent.activity,
            supporting_sql=agent.supporting_sql,
            critic_passed=agent.critic_passed,
            critic_feedback=agent.critic_feedback,
            failure_type=agent.failure_type,
            recovery_action=agent.recovery_action,
            recovery_history=agent.recovery_history,
            iteration=agent.iteration,
            model=agent.model,
            query_result=agent.query_result,
            python_result=agent.python_result,
            charts=agent.charts,
            chart_paths=agent.chart_paths,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
