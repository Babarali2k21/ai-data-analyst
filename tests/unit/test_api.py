from pathlib import Path

from fastapi.testclient import TestClient

from ai_data_analyst.agent.graph import AgentResult
from ai_data_analyst.analyst.sql_pipeline import SQLAnalystResult
from ai_data_analyst.api.app import create_app
from ai_data_analyst.config import Settings
from ai_data_analyst.tools.sql import QueryResult


def _settings(tmp_path: Path, duckdb: Path) -> Settings:
    return Settings(
        duckdb_path=duckdb,
        olist_raw_dir=tmp_path / "raw",
        olist_metadata_dir=tmp_path / "meta",
        charts_dir=tmp_path / "charts",
        openai_api_key="sk-test",
        llm_model="gpt-4.1-mini",
    )


def test_health_degraded_without_duckdb(tmp_path: Path, monkeypatch: object) -> None:
    settings = _settings(tmp_path, tmp_path / "missing.duckdb")
    monkeypatch.setattr("ai_data_analyst.api.deps.get_settings", lambda: settings)
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["duckdb_ready"] is False
    assert body["status"] == "degraded"


def test_analysis_agent_success(tmp_path: Path, monkeypatch: object) -> None:
    duckdb = tmp_path / "analytics.duckdb"
    duckdb.write_bytes(b"not-empty")
    settings = _settings(tmp_path, duckdb)
    monkeypatch.setattr("ai_data_analyst.api.deps.get_settings", lambda: settings)
    monkeypatch.setattr("ai_data_analyst.config.get_settings", lambda: settings)

    def fake_agent(question: str, **_kwargs: object) -> AgentResult:
        return AgentResult(
            question=question,
            answer="There are 3 orders.",
            sql="SELECT count(*) AS n FROM orders",
            plan={"tool": "sql"},
            activity=["Planned", "SQL", "Critic passed"],
            critic_passed=True,
            iteration=1,
            model="gpt-4.1-mini",
            query_result={"columns": ["n"], "rows": [{"n": 3}], "row_count": 1},
            charts=[{"type": "bar", "x": "a", "y": "b", "title": "t"}],
        )

    monkeypatch.setattr(
        "ai_data_analyst.api.routes.analysis.run_analyst_agent",
        fake_agent,
    )
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/analysis",
        json={"question": "How many orders?", "mode": "agent"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "There are 3 orders."
    assert body["mode"] == "agent"
    assert body["critic_passed"] is True
    assert body["charts"]
    assert body["observability"]["run_id"]
    assert "X-Request-Id" in response.headers


def test_analysis_sql_mode(tmp_path: Path, monkeypatch: object) -> None:
    duckdb = tmp_path / "analytics.duckdb"
    duckdb.write_bytes(b"not-empty")
    settings = _settings(tmp_path, duckdb)
    monkeypatch.setattr("ai_data_analyst.api.deps.get_settings", lambda: settings)

    def fake_sql(question: str, **_kwargs: object) -> SQLAnalystResult:
        return SQLAnalystResult(
            question=question,
            sql="SELECT 1 AS n",
            answer="1",
            query_result=QueryResult(
                sql="SELECT 1 AS n",
                columns=["n"],
                rows=[{"n": 1}],
                row_count=1,
            ),
            model="gpt-4.1-mini",
            attempts=1,
        )

    monkeypatch.setattr("ai_data_analyst.api.routes.analysis.ask_sql", fake_sql)
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/analysis",
        json={"question": "Select one", "mode": "sql"},
    )
    assert response.status_code == 200
    assert response.json()["mode"] == "sql"
    assert response.json()["answer"] == "1"


def test_analysis_requires_api_key(tmp_path: Path, monkeypatch: object) -> None:
    duckdb = tmp_path / "analytics.duckdb"
    duckdb.write_bytes(b"not-empty")
    settings = _settings(tmp_path, duckdb)
    settings.openai_api_key = ""
    monkeypatch.setattr("ai_data_analyst.api.deps.get_settings", lambda: settings)
    client = TestClient(create_app())
    response = client.post("/api/v1/analysis", json={"question": "How many orders?"})
    assert response.status_code == 503
