"""Health and dataset info routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from ai_data_analyst.api.deps import settings_dep
from ai_data_analyst.api.schemas import DatasetInfoResponse, HealthResponse
from ai_data_analyst.config import Settings
from ai_data_analyst.data.duckdb import list_tables

router = APIRouter(tags=["system"])
SettingsDep = Annotated[Settings, Depends(settings_dep)]


@router.get("/health", response_model=HealthResponse)
@router.get("/api/v1/health", response_model=HealthResponse)
def health(settings: SettingsDep) -> HealthResponse:
    ready = settings.duckdb_ready
    return HealthResponse(
        status="ok" if ready else "degraded",
        duckdb_ready=ready,
        model=settings.llm_model,
        auth_required=settings.auth_required,
    )


@router.get("/api/v1/dataset", response_model=DatasetInfoResponse)
def dataset_info(settings: SettingsDep) -> DatasetInfoResponse:
    tables: list[str] = []
    if settings.duckdb_ready:
        tables = list_tables(path=settings.duckdb_path)
    return DatasetInfoResponse(
        dataset="olist",
        tables=tables,
        duckdb_path=str(settings.duckdb_path),
    )
