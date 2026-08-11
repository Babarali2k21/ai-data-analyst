"""API dependencies."""

from __future__ import annotations

from ai_data_analyst.config import Settings, get_settings


def settings_dep() -> Settings:
    return get_settings()
