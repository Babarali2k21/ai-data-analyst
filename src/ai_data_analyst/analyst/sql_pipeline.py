"""Phase 2: question → SQL → execute → natural-language answer."""

from __future__ import annotations

import argparse
import re

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from ai_data_analyst.analyst.context import build_schema_context
from ai_data_analyst.analyst.prompts import (
    ANSWER_SYSTEM_PROMPT,
    SQL_SYSTEM_PROMPT,
    answer_user_prompt,
    sql_user_prompt,
)
from ai_data_analyst.config import Settings, get_settings
from ai_data_analyst.llm.client import get_chat_model
from ai_data_analyst.tools.preview import preview_query_result
from ai_data_analyst.tools.sql import QueryResult, run_sql
from ai_data_analyst.tools.sql_validation import SQLValidationError, validate_sql

_FENCE_RE = re.compile(r"```(?:sql)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


class SQLAnalystResult(BaseModel):
    question: str
    sql: str
    answer: str
    query_result: QueryResult
    model: str
    attempts: int = 1


def extract_sql(text: str) -> str:
    """Pull SQL out of model output (raw or fenced)."""
    text = text.strip()
    fence = _FENCE_RE.search(text)
    if fence:
        return fence.group(1).strip()
    return text


def generate_sql(
    question: str,
    *,
    schema_context: str,
    llm: BaseChatModel,
) -> str:
    messages = [
        SystemMessage(content=SQL_SYSTEM_PROMPT),
        HumanMessage(content=sql_user_prompt(question, schema_context)),
    ]
    response = llm.invoke(messages)
    content = response.content
    if not isinstance(content, str):
        content = str(content)
    return extract_sql(content)


def repair_sql(
    question: str,
    *,
    schema_context: str,
    llm: BaseChatModel,
    previous_sql: str = "",
    error: str = "",
    critic_feedback: str = "",
) -> str:
    """Ask the LLM for a corrected DuckDB SELECT/WITH query."""
    repair_prompt = (
        f"{sql_user_prompt(question, schema_context)}\n\n"
        f"Critic feedback:\n{critic_feedback or '(none)'}\n\n"
        f"Previous error:\n{error or '(none)'}\n\n"
        f"Previous SQL:\n{previous_sql or '(none)'}\n\n"
        "Write a corrected single DuckDB SELECT/WITH query only."
    )
    response = llm.invoke(
        [
            SystemMessage(content=SQL_SYSTEM_PROMPT),
            HumanMessage(content=repair_prompt),
        ]
    )
    content = response.content
    if not isinstance(content, str):
        content = str(content)
    return extract_sql(content)


def summarize_answer(
    question: str,
    sql: str,
    result: QueryResult,
    *,
    llm: BaseChatModel,
) -> str:
    messages = [
        SystemMessage(content=ANSWER_SYSTEM_PROMPT),
        HumanMessage(
            content=answer_user_prompt(question, sql, preview_query_result(result, max_rows=20))
        ),
    ]
    response = llm.invoke(messages)
    content = response.content
    if not isinstance(content, str):
        content = str(content)
    return content.strip()


def ask_sql(
    question: str,
    *,
    settings: Settings | None = None,
    llm: BaseChatModel | None = None,
    max_attempts: int = 2,
) -> SQLAnalystResult:
    """Run the Phase 2 SQL analyst pipeline with one repair attempt on SQL errors."""
    settings = settings or get_settings()
    llm = llm or get_chat_model(settings)
    schema_context = build_schema_context(settings)

    last_error: str | None = None
    sql = ""
    for attempt in range(1, max_attempts + 1):
        if attempt == 1:
            sql = generate_sql(question, schema_context=schema_context, llm=llm)
        else:
            sql = repair_sql(
                question,
                schema_context=schema_context,
                llm=llm,
                previous_sql=sql,
                error=last_error or "",
            )

        try:
            validate_sql(sql)
            query_result = run_sql(sql, settings=settings)
            answer = summarize_answer(question, query_result.sql, query_result, llm=llm)
            return SQLAnalystResult(
                question=question,
                sql=query_result.sql,
                answer=answer,
                query_result=query_result,
                model=settings.llm_model,
                attempts=attempt,
            )
        except (SQLValidationError, Exception) as exc:  # noqa: BLE001 — repair loop
            last_error = str(exc)
            if attempt >= max_attempts:
                raise RuntimeError(
                    f"SQL analyst failed after {attempt} attempt(s): {last_error}\nSQL:\n{sql}"
                ) from exc

    raise RuntimeError("SQL analyst failed unexpectedly")


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 2 SQL analyst (question → SQL → answer)")
    parser.add_argument("question", nargs="+", help="Natural language analytics question")
    parser.add_argument("--json", action="store_true", help="Print full JSON result")
    args = parser.parse_args()
    question = " ".join(args.question)

    result = ask_sql(question)
    if args.json:
        print(result.model_dump_json(indent=2))
        return

    print(f"Model: {result.model}")
    print(f"Attempts: {result.attempts}")
    print("\nSQL:")
    print(result.sql)
    print("\nAnswer:")
    print(result.answer)
    print(f"\nRows returned: {len(result.query_result.rows)} / {result.query_result.row_count}")
    if result.query_result.truncated:
        print("(result truncated)")


if __name__ == "__main__":
    main()
