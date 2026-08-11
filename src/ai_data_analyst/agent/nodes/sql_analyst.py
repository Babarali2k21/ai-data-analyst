"""SQL analyst node: generate and execute DuckDB SQL."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from ai_data_analyst.agent.state import AnalystState
from ai_data_analyst.analyst.sql_pipeline import generate_sql, repair_sql, summarize_answer
from ai_data_analyst.config import Settings
from ai_data_analyst.tools.sql import run_sql
from ai_data_analyst.tools.sql_validation import SQLValidationError, validate_sql


def make_sql_analyst_node(llm: BaseChatModel, settings: Settings) -> Any:
    def sql_analyst(state: AnalystState) -> dict[str, Any]:
        question = state["question"]
        schema_context = state.get("schema_context") or ""
        feedback = state.get("critic_feedback") or ""
        prior_sql = state.get("sql") or ""
        prior_error = state.get("error") or ""

        try:
            if feedback or prior_error:
                sql = repair_sql(
                    question,
                    schema_context=schema_context,
                    llm=llm,
                    previous_sql=prior_sql,
                    error=prior_error,
                    critic_feedback=feedback,
                )
            else:
                sql = generate_sql(question, schema_context=schema_context, llm=llm)

            validate_sql(sql)
            result = run_sql(sql, settings=settings)
            findings = summarize_answer(question, result.sql, result, llm=llm)
            supporting = list(state.get("supporting_sql") or [])
            supporting.append(result.sql)
            return {
                "sql": result.sql,
                "query_result": result.model_dump(),
                "findings": findings,
                "error": "",
                "supporting_sql": supporting,
                "activity": ["Generated and executed SQL"],
            }
        except (SQLValidationError, Exception) as exc:  # noqa: BLE001
            return {
                "sql": state.get("sql") or "",
                "query_result": {},
                "findings": "",
                "error": str(exc),
                "activity": [f"SQL analyst error: {exc}"],
            }

    return sql_analyst
