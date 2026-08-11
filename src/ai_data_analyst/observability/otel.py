"""Optional OpenTelemetry hooks (no-op unless OTEL packages + env are configured)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("ai_data_analyst.otel")


def instrument_app(app: Any) -> bool:
    """Try to instrument FastAPI with OpenTelemetry.

    Returns True when instrumentation was applied. Safe to call when OTel is absent.
    """
    try:
        from opentelemetry.instrumentation.fastapi import (  # type: ignore[import-not-found]
            FastAPIInstrumentor,
        )
    except ImportError:
        logger.debug("opentelemetry-instrumentation-fastapi not installed; skipping")
        return False

    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("OpenTelemetry FastAPI instrumentation enabled")
        return True
    except Exception:  # noqa: BLE001
        logger.exception("Failed to enable OpenTelemetry instrumentation")
        return False
