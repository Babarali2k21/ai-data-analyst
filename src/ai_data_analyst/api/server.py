"""Uvicorn entrypoint for the FastAPI server."""

from __future__ import annotations

import uvicorn

from ai_data_analyst.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "ai_data_analyst.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )


if __name__ == "__main__":
    main()
