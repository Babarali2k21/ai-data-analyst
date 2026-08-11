"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from ai_data_analyst.api.routes import analysis, system
from ai_data_analyst.config import get_settings
from ai_data_analyst.observability.logging import configure_logging
from ai_data_analyst.observability.middleware import RequestContextMiddleware
from ai_data_analyst.observability.otel import instrument_app


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="AI Data Analyst API",
        description="Analyze the Olist e-commerce dataset with SQL, Python stats, and LangGraph.",
        version="0.1.0",
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(system.router)
    app.include_router(analysis.router)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    charts_dir = settings.charts_dir
    charts_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/charts", StaticFiles(directory=str(charts_dir)), name="charts")
    instrument_app(app)

    return app


app = create_app()
