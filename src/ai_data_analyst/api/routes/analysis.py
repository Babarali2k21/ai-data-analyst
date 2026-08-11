"""Analysis API routes — HTTP adapter only."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ai_data_analyst.api.deps import enforce_access, settings_dep
from ai_data_analyst.api.schemas import AnalysisRequest, AnalysisResponse
from ai_data_analyst.api.services.analysis import (
    AnalysisNotReadyError,
    AnalysisTimeoutError,
    run_analysis,
)
from ai_data_analyst.config import Settings

router = APIRouter(prefix="/api/v1", tags=["analysis"])
SettingsDep = Annotated[Settings, Depends(settings_dep)]


@router.post("/analysis", response_model=AnalysisResponse)
def create_analysis(
    body: AnalysisRequest,
    settings: SettingsDep,
    _access: Annotated[str | None, Depends(enforce_access)],
) -> AnalysisResponse:
    """Run the SQL pipeline or full LangGraph analyst agent."""
    try:
        return run_analysis(body.question, mode=body.mode, settings=settings)
    except (AnalysisNotReadyError, AnalysisTimeoutError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
