from ai_data_analyst.agent.recovery import classify_tool_error, rule_based_critic


def test_classify_schema_error_retries_sql() -> None:
    verdict = classify_tool_error(
        'Catalog Error: Table with name "orderz" does not exist!',
        "sql",
    )
    assert verdict.passed is False
    assert verdict.failure_type == "schema_mismatch"
    assert verdict.recovery_action == "retry_sql"


def test_classify_syntax_error_retries_python_route() -> None:
    verdict = classify_tool_error("Parser Error: syntax error near SELECT", "python")
    assert verdict.failure_type == "tool_error"
    assert verdict.recovery_action == "retry_python"


def test_rule_based_missing_findings() -> None:
    result = rule_based_critic({"question": "q", "error": "", "findings": ""})
    assert result.triggered is True
    assert result.verdict is not None
    assert result.verdict.failure_type == "missing_findings"
    assert result.verdict.recovery_action == "replan"


def test_rule_based_empty_result_short_findings() -> None:
    result = rule_based_critic(
        {
            "question": "q",
            "error": "",
            "findings": "None",
            "route": "sql",
            "query_result": {"row_count": 0, "rows": []},
            "python_result": {},
        }
    )
    assert result.triggered is True
    assert result.verdict is not None
    assert result.verdict.failure_type == "empty_result"
    assert result.verdict.recovery_action == "retry_sql"


def test_rule_based_passes_through_to_llm() -> None:
    result = rule_based_critic(
        {
            "question": "q",
            "error": "",
            "findings": "There were 10 delivered orders in January based on the query.",
            "route": "sql",
            "query_result": {"row_count": 1, "rows": [{"n": 10}]},
        }
    )
    assert result.triggered is False
