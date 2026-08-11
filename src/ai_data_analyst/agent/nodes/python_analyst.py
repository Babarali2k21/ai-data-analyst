"""Python analyst node (Phase 3 stub; full stats tools arrive in Phase 4)."""

from __future__ import annotations

from typing import Any

from ai_data_analyst.agent.state import AnalystState


def python_analyst(state: AnalystState) -> dict[str, Any]:
    """Placeholder until Phase 4 statistical tools land.

    Signals the critic/planner to fall back to SQL for now.
    """
    return {
        "findings": "",
        "error": (
            "Python/statistical analyst is not implemented yet (Phase 4). "
            "Replan using tool=sql to answer with DuckDB."
        ),
        "activity": ["Python analyst unavailable — requesting SQL replan"],
    }
