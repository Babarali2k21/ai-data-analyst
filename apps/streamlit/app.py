"""Streamlit live demo for the Olist autonomous data analyst.

Deploy on Streamlit Community Cloud:
  Main file: apps/streamlit/app.py
  Secrets: OPENAI_API_KEY (and optional DEMO_QUERY_LIMIT=3)
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

# Allow `streamlit run apps/streamlit/app.py` without editable install.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st

from ai_data_analyst.agent.graph import run_analyst_agent
from ai_data_analyst.analyst.sql_pipeline import ask_sql
from ai_data_analyst.config import Settings, get_settings
from ai_data_analyst.demo.bootstrap import ensure_demo_database
from ai_data_analyst.observability.context import start_run_metrics
from ai_data_analyst.observability.logging import configure_logging
from ai_data_analyst.security.demo_quota import (
    fingerprint_visitor,
    get_demo_quota_store,
)

SAMPLE_QUESTIONS = [
    "How many orders are in the dataset?",
    "What is the average payment value?",
    "Which product categories appear most often?",
]


def _load_settings() -> Settings:
    # Streamlit Cloud secrets override env when present.
    secrets = getattr(st, "secrets", {})
    try:
        openai_key = str(secrets.get("OPENAI_API_KEY", "") or "")
        model = str(secrets.get("LLM_MODEL", "") or "")
        limit_raw = secrets.get("DEMO_QUERY_LIMIT", None)
    except Exception:  # noqa: BLE001 — secrets may be unavailable locally
        openai_key = ""
        model = ""
        limit_raw = None

    base = get_settings()
    updates: dict[str, object] = {}
    if openai_key:
        updates["openai_api_key"] = openai_key
    if model:
        updates["llm_model"] = model
    if limit_raw is not None and str(limit_raw).strip():
        updates["demo_query_limit"] = int(limit_raw)

    duckdb = ensure_demo_database(base)
    updates["duckdb_path"] = duckdb
    updates["charts_dir"] = duckdb.parent / "charts"
    return base.model_copy(update=updates)


def _client_ip() -> str | None:
    try:
        headers = st.context.headers
    except Exception:  # noqa: BLE001
        return None
    forwarded = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return headers.get("X-Real-Ip") or headers.get("x-real-ip")


def _ensure_visitor_cookie() -> str:
    params = st.query_params
    existing = params.get("vid")
    if isinstance(existing, list):
        existing = existing[0] if existing else None
    if existing and isinstance(existing, str) and len(existing) >= 8:
        st.session_state["vid"] = existing
        return existing
    if "vid" not in st.session_state:
        st.session_state["vid"] = uuid.uuid4().hex[:16]
    st.query_params["vid"] = st.session_state["vid"]
    return str(st.session_state["vid"])


def main() -> None:
    st.set_page_config(
        page_title="AI Data Analyst — Olist Demo",
        page_icon="📊",
        layout="wide",
    )
    configure_logging("INFO")
    settings = _load_settings()
    limit = max(1, int(settings.demo_query_limit))

    cookie = _ensure_visitor_cookie()
    visitor = fingerprint_visitor(ip=_client_ip(), cookie=cookie)
    store = get_demo_quota_store(settings)
    quota = store.status(visitor, limit=limit)

    st.title("Autonomous Data Analyst")
    st.caption(
        "Olist e-commerce demo — SQL + LangGraph agent. "
        f"Public demo limit: **{limit} queries per visitor** to protect API spend."
    )

    left, right = st.columns([2, 1])
    with right:
        st.metric("Queries remaining", f"{quota.remaining} / {limit}")
        st.write(f"Model: `{settings.llm_model}`")
        st.write(f"Database: `{settings.duckdb_path.name}`")
        if not quota.allowed:
            st.error("Demo quota exhausted for this visitor. Thanks for trying it!")
            st.stop()

    with left:
        mode = st.radio(
            "Mode",
            options=["sql", "agent"],
            horizontal=True,
            help="SQL mode is cheaper. Agent mode adds planning, critic, and charts.",
            index=0,
        )
        question = st.selectbox("Try a sample question", options=[""] + SAMPLE_QUESTIONS)
        custom = st.text_area(
            "Or write your own",
            value="" if question else st.session_state.get("last_q", ""),
            height=100,
            placeholder="e.g. How many orders are in the dataset?",
        )
        final_q = (custom or question or "").strip()
        run = st.button(
            "Run analysis",
            type="primary",
            disabled=not final_q or not quota.allowed,
        )

    if not settings.openai_api_key:
        st.warning(
            "OPENAI_API_KEY is not set. Add it under Streamlit **Secrets** "
            "or your local `.env`."
        )
        st.stop()

    if not run:
        st.info(
            "This public demo uses a small fixture subset of Olist so the app "
            "stays lightweight on Streamlit Cloud."
        )
        return

    # Consume quota before calling the LLM so refreshes cannot free a slot.
    consumed = store.consume(visitor, limit=limit)
    if not consumed.allowed:
        st.error("Demo quota exhausted for this visitor.")
        st.stop()

    st.session_state["last_q"] = final_q
    start_run_metrics()
    with st.spinner(f"Running {mode} analysis… ({consumed.remaining} left after this)"):
        try:
            if mode == "sql":
                result = ask_sql(final_q, settings=settings)
                answer = result.answer
                activity = [f"SQL attempts: {result.attempts}"]
                sqls = [result.sql] if result.sql else []
                charts: list[str] = []
                critic = None
            else:
                result = run_analyst_agent(final_q, settings=settings)
                answer = result.answer
                activity = list(result.activity)
                sqls = list(result.supporting_sql or ([result.sql] if result.sql else []))
                charts = list(result.chart_paths or [])
                critic = result.critic_passed
        except Exception as exc:  # noqa: BLE001
            st.exception(exc)
            return

    st.subheader("Findings")
    st.write(answer)
    if critic is not None:
        st.write(f"Critic passed: `{critic}`")

    if activity:
        st.subheader("Activity")
        for step in activity:
            st.write(f"- {step}")

    if sqls:
        st.subheader("Supporting SQL")
        for sql in sqls:
            st.code(sql, language="sql")

    if charts:
        st.subheader("Charts")
        for path in charts:
            p = Path(path)
            if p.exists():
                st.image(str(p))


if __name__ == "__main__":
    main()
