from typing import Any

from langchain_core.messages import AIMessage

from ai_data_analyst.analyst.sql_pipeline import ask_sql
from ai_data_analyst.config import Settings
from ai_data_analyst.data.ingestion.olist import ingest_olist


class FakeLLM:
    """Minimal chat model stub: first call returns SQL, second returns answer."""

    def __init__(self, sql: str = "SELECT count(*) AS n FROM orders") -> None:
        self.sql = sql
        self.calls = 0

    def invoke(self, messages: Any) -> AIMessage:
        self.calls += 1
        if self.calls == 1:
            return AIMessage(content=self.sql)
        return AIMessage(content="There are 3 orders in the fixture dataset.")


def test_ask_sql_with_fake_llm(temp_settings: Settings) -> None:
    ingest_olist(settings=temp_settings)
    llm = FakeLLM()
    result = ask_sql(
        "How many orders are there?",
        settings=temp_settings,
        llm=llm,  # type: ignore[arg-type]
    )
    assert result.sql.lower().startswith("select")
    assert result.query_result.rows[0]["n"] == 3
    assert "3" in result.answer
    assert result.attempts == 1
    assert llm.calls == 2
