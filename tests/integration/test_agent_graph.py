from typing import Any

from langchain_core.messages import AIMessage

from ai_data_analyst.agent.graph import run_analyst_agent
from ai_data_analyst.agent.state import AnalysisPlan, CriticVerdict
from ai_data_analyst.config import Settings
from ai_data_analyst.data.ingestion.olist import ingest_olist


class FakeLLM:
    """Deterministic stand-in for ChatOpenAI + structured outputs."""

    def __init__(self, tool: str = "sql") -> None:
        self.tool = tool
        self.invoke_calls = 0

    def with_structured_output(self, schema: type[Any]) -> Any:
        parent = self

        class Structured:
            def invoke(self, _messages: Any) -> Any:
                if schema is AnalysisPlan:
                    return AnalysisPlan(
                        goal="Count orders",
                        steps=["Query orders table", "Return count"],
                        tool=parent.tool,  # type: ignore[arg-type]
                        rationale="Simple aggregation",
                    )
                if schema is CriticVerdict:
                    # Pass once we have SQL findings; fail python stub path
                    return CriticVerdict(passed=parent.tool == "sql", feedback="ok")
                raise TypeError(f"Unexpected schema {schema}")

        return Structured()

    def invoke(self, messages: Any) -> AIMessage:
        self.invoke_calls += 1
        contents: list[str] = []
        for message in messages:
            content = getattr(message, "content", message)
            contents.append(content if isinstance(content, str) else str(content))
        blob = "\n".join(contents).lower()
        # SQL generation / repair prompts end with "SQL:" and include schema
        if "write a corrected" in blob or blob.rstrip().endswith("sql:"):
            return AIMessage(content="SELECT count(*) AS n FROM orders")
        if "schema:" in blob and "question:" in blob and "result:" not in blob:
            return AIMessage(content="SELECT count(*) AS n FROM orders")
        return AIMessage(content="There are 3 orders in the dataset.")


def test_agent_sql_path_with_fake_llm(temp_settings: Settings) -> None:
    ingest_olist(settings=temp_settings)
    # Keep agent loops small in tests
    temp_settings.max_agent_iterations = 2
    llm = FakeLLM(tool="sql")
    result = run_analyst_agent(
        "How many orders are there?",
        settings=temp_settings,
        llm=llm,  # type: ignore[arg-type]
    )
    assert result.critic_passed is True
    assert result.answer
    assert result.sql
    assert "Generated and executed SQL" in result.activity
    assert result.iteration >= 1


def test_agent_python_stub_replans_or_finalizes(temp_settings: Settings) -> None:
    ingest_olist(settings=temp_settings)
    temp_settings.max_agent_iterations = 1
    llm = FakeLLM(tool="python")
    result = run_analyst_agent(
        "Compute correlation of price and freight",
        settings=temp_settings,
        llm=llm,  # type: ignore[arg-type]
    )
    # With max_iterations=1, python stub fails critic then finalizer runs
    assert result.critic_passed is False
    assert "Python" in result.critic_feedback or result.answer
    assert any("Python" in step for step in result.activity)
