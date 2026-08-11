from typing import Any

from langchain_core.messages import AIMessage

from ai_data_analyst.agent.graph import run_analyst_agent
from ai_data_analyst.agent.state import AnalysisPlan, CriticVerdict
from ai_data_analyst.config import Settings
from ai_data_analyst.data.ingestion.olist import ingest_olist
from ai_data_analyst.tools.charts import ChartProposal
from ai_data_analyst.tools.stats import StatsSpec


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
                        goal="Analyze data",
                        steps=["Fetch data", "Compute metric"],
                        tool=parent.tool,  # type: ignore[arg-type]
                        rationale="test",
                    )
                if schema is CriticVerdict:
                    return CriticVerdict(passed=True, feedback="ok")
                if schema is StatsSpec:
                    return StatsSpec(
                        operation="correlation",
                        data_sql="SELECT price, freight_value FROM order_items",
                        columns=["price", "freight_value"],
                        rationale="correlation of price and freight",
                    )
                if schema is ChartProposal:
                    if parent.tool == "python":
                        return ChartProposal(
                            should_chart=True,
                            type="scatter",
                            x="price",
                            y="freight_value",
                            title="Price vs freight",
                        )
                    return ChartProposal(should_chart=False, reason="scalar count")
                raise TypeError(f"Unexpected schema {schema}")

        return Structured()

    def invoke(self, messages: Any) -> AIMessage:
        self.invoke_calls += 1
        contents: list[str] = []
        for message in messages:
            content = getattr(message, "content", message)
            contents.append(content if isinstance(content, str) else str(content))
        blob = "\n".join(contents).lower()
        if "stats summary" in blob:
            return AIMessage(content="Price and freight are positively correlated.")
        if "write a corrected" in blob or blob.rstrip().endswith("sql:"):
            return AIMessage(content="SELECT count(*) AS n FROM orders")
        if "schema:" in blob and "question:" in blob and "result:" not in blob:
            return AIMessage(content="SELECT count(*) AS n FROM orders")
        return AIMessage(content="There are 3 orders in the dataset.")


def test_agent_sql_path_with_fake_llm(temp_settings: Settings) -> None:
    ingest_olist(settings=temp_settings)
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
    assert any("visualization" in step.lower() for step in result.activity)
    assert result.iteration >= 1


def test_agent_python_stats_path(temp_settings: Settings) -> None:
    ingest_olist(settings=temp_settings)
    temp_settings.max_agent_iterations = 2
    llm = FakeLLM(tool="python")
    result = run_analyst_agent(
        "What is the correlation between price and freight_value?",
        settings=temp_settings,
        llm=llm,  # type: ignore[arg-type]
    )
    assert result.critic_passed is True
    assert result.python_result.get("operation") == "correlation"
    assert "matrix" in (result.python_result.get("summary") or {})
    assert any("statistical analysis" in step.lower() for step in result.activity)
    assert "correlated" in result.answer.lower() or result.answer
    assert result.charts
    assert result.charts[0]["type"] == "scatter"
