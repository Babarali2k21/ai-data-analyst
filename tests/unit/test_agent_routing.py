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


def test_route_after_critic_pass_and_max_iterations() -> None:
    settings = Settings(
        duckdb_path="/tmp/x.duckdb",
        olist_raw_dir="/tmp/raw",
        olist_metadata_dir="/tmp/meta",
        max_agent_iterations=2,
    )
    assert (
        route_after_critic(
            {"question": "q", "critic_passed": True, "iteration": 1},
            settings,
        )
        == "finalizer"
    )
    assert (
        route_after_critic(
            {
                "question": "q",
                "critic_passed": False,
                "iteration": 2,
                "recovery_action": "retry_sql",
            },
            settings,
        )
        == "finalizer"
    )


def test_route_after_critic_direct_retry_and_replan() -> None:
    settings = Settings(
        duckdb_path="/tmp/x.duckdb",
        olist_raw_dir="/tmp/raw",
        olist_metadata_dir="/tmp/meta",
        max_agent_iterations=3,
    )
    assert (
        route_after_critic(
            {
                "question": "q",
                "critic_passed": False,
                "iteration": 1,
                "recovery_action": "retry_sql",
                "failure_type": "tool_error",
                "recovery_history": ["tool_error:retry_sql"],
            },
            settings,
        )
        == "sql_analyst"
    )
    assert (
        route_after_critic(
            {
                "question": "q",
                "critic_passed": False,
                "iteration": 1,
                "recovery_action": "retry_python",
                "failure_type": "tool_error",
                "recovery_history": ["tool_error:retry_python"],
            },
            settings,
        )
        == "python_analyst"
    )
    assert (
        route_after_critic(
            {
                "question": "q",
                "critic_passed": False,
                "iteration": 1,
                "recovery_action": "switch_to_sql",
                "failure_type": "wrong_tool",
                "recovery_history": ["wrong_tool:switch_to_sql"],
            },
            settings,
        )
        == "planner"
    )
    # Escalate after repeated identical retries
    assert (
        route_after_critic(
            {
                "question": "q",
                "critic_passed": False,
                "iteration": 1,
                "recovery_action": "retry_sql",
                "failure_type": "tool_error",
                "recovery_history": ["tool_error:retry_sql", "tool_error:retry_sql"],
            },
            settings,
        )
        == "planner"
    )
