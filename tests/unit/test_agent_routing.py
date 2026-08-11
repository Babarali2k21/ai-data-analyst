from ai_data_analyst.agent.nodes.critic import route_after_critic
from ai_data_analyst.agent.nodes.router import route_after_planner, router
from ai_data_analyst.config import Settings


def test_router_sets_sql_route() -> None:
    out = router({"question": "q", "plan": {"tool": "sql"}})
    assert out["route"] == "sql"
    assert route_after_planner({**out, "question": "q"}) == "sql_analyst"


def test_router_sets_python_route() -> None:
    out = router({"question": "q", "plan": {"tool": "python"}})
    assert out["route"] == "python"
    assert route_after_planner({**out, "question": "q"}) == "python_analyst"


def test_route_after_critic_respects_max_iterations() -> None:
    settings = Settings(
        duckdb_path="/tmp/x.duckdb",
        olist_raw_dir="/tmp/raw",
        olist_metadata_dir="/tmp/meta",
        max_agent_iterations=2,
    )
    assert (
        route_after_critic(
            {"question": "q", "critic_passed": False, "iteration": 2},
            settings,
        )
        == "finalizer"
    )
    assert (
        route_after_critic(
            {"question": "q", "critic_passed": False, "iteration": 1},
            settings,
        )
        == "planner"
    )
    assert (
        route_after_critic(
            {"question": "q", "critic_passed": True, "iteration": 1},
            settings,
        )
        == "finalizer"
    )
