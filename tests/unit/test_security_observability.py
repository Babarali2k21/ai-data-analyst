"""Unit tests for Phase 10 API security and observability."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient

from ai_data_analyst.agent.graph import AgentResult
from ai_data_analyst.api.app import create_app
from ai_data_analyst.api.deps import reset_rate_limiter
from ai_data_analyst.config import Settings
from ai_data_analyst.observability.context import RunMetrics, start_run_metrics
from ai_data_analyst.security.auth import extract_api_key, require_api_key
from ai_data_analyst.security.rate_limit import RateLimiter


def _settings(tmp_path: Path, duckdb: Path, **kwargs: object) -> Settings:
    return Settings(
        duckdb_path=duckdb,
        olist_raw_dir=tmp_path / "raw",
        olist_metadata_dir=tmp_path / "meta",
        charts_dir=tmp_path / "charts",
        openai_api_key="sk-test",
        llm_model="gpt-4.1-mini",
        **kwargs,  # type: ignore[arg-type]
    )


def _patch_settings(monkeypatch: object, settings: Settings) -> None:
    monkeypatch.setattr("ai_data_analyst.api.deps.get_settings", lambda: settings)
    monkeypatch.setattr("ai_data_analyst.config.get_settings", lambda: settings)
    reset_rate_limiter()


def test_extract_api_key_prefers_x_api_key() -> None:
    assert extract_api_key("Bearer ignored", "from-header") == "from-header"
    assert extract_api_key("Bearer tok", None) == "tok"
    assert extract_api_key(None, None) is None


def test_require_api_key_disabled() -> None:
    settings = Settings(api_keys=[])
    assert require_api_key(settings) is None


def test_require_api_key_rejects_missing() -> None:
    settings = Settings(api_keys=["secret"])
    try:
        require_api_key(settings)
        raise AssertionError("expected HTTPException")
    except HTTPException as exc:
        assert exc.status_code == 401


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = RateLimiter(limit=2, window_seconds=60)
    limiter.check("ip:1")
    limiter.check("ip:1")
    try:
        limiter.check("ip:1")
        raise AssertionError("expected HTTPException")
    except HTTPException as exc:
        assert exc.status_code == 429


def test_run_metrics_as_dict() -> None:
    metrics = start_run_metrics(request_id="req_test")
    metrics.mark_sql(12.5)
    metrics.mark_llm(33.0, prompt_tokens=10, completion_tokens=5)
    payload = metrics.as_dict()
    assert payload["request_id"] == "req_test"
    assert payload["sql_calls"] == 1
    assert payload["llm_calls"] == 1
    assert payload["total_tokens"] == 15
    assert "estimated_cost_usd" in payload


def test_health_reports_auth_required(tmp_path: Path, monkeypatch: object) -> None:
    settings = _settings(tmp_path, tmp_path / "missing.duckdb", api_keys=["k"])
    _patch_settings(monkeypatch, settings)
    client = TestClient(create_app())
    body = client.get("/health").json()
    assert body["auth_required"] is True


def test_analysis_requires_api_key_header(tmp_path: Path, monkeypatch: object) -> None:
    duckdb = tmp_path / "analytics.duckdb"
    duckdb.write_bytes(b"not-empty")
    settings = _settings(tmp_path, duckdb, api_keys=["good-key"])
    _patch_settings(monkeypatch, settings)

    monkeypatch.setattr(
        "ai_data_analyst.api.routes.analysis.run_analyst_agent",
        lambda question, **_: AgentResult(question=question, answer="ok", model="m"),
    )
    client = TestClient(create_app())
    denied = client.post("/api/v1/analysis", json={"question": "How many orders?"})
    assert denied.status_code == 401

    ok = client.post(
        "/api/v1/analysis",
        json={"question": "How many orders?"},
        headers={"X-API-Key": "good-key"},
    )
    assert ok.status_code == 200
    assert "observability" in ok.json()
    assert ok.json()["observability"]["run_id"]
    assert "X-Request-Id" in ok.headers


def test_analysis_rate_limited(tmp_path: Path, monkeypatch: object) -> None:
    duckdb = tmp_path / "analytics.duckdb"
    duckdb.write_bytes(b"not-empty")
    settings = _settings(tmp_path, duckdb, api_rate_limit_per_minute=2)
    _patch_settings(monkeypatch, settings)

    monkeypatch.setattr(
        "ai_data_analyst.api.routes.analysis.run_analyst_agent",
        lambda question, **_: AgentResult(question=question, answer="ok", model="m"),
    )
    client = TestClient(create_app())
    payload = {"question": "How many orders?"}
    assert client.post("/api/v1/analysis", json=payload).status_code == 200
    assert client.post("/api/v1/analysis", json=payload).status_code == 200
    assert client.post("/api/v1/analysis", json=payload).status_code == 429


def test_observability_info_defaults() -> None:
    metrics = RunMetrics(run_id="run_abc")
    assert metrics.total_tokens == 0
    assert metrics.estimate_cost_usd() == 0.0
