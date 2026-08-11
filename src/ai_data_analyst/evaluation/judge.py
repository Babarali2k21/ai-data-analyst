"""LLM-as-judge for free-form analytical answers."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

JUDGE_SYSTEM = """\
You are an evaluation judge for an analytics agent answering questions about the Olist dataset.
Decide if the answer is factually consistent with the provided SQL/stats evidence.
Pass if the answer is reasonably correct and grounded. Fail if it invents numbers,
contradicts the evidence, or misses the question.
"""


class JudgeVerdict(BaseModel):
    correct: bool
    hallucinated: bool = False
    rationale: str = Field(default="")


def judge_answer(
    llm: BaseChatModel,
    *,
    question: str,
    answer: str,
    sql: str | None,
    query_result: dict[str, Any] | None,
    python_result: dict[str, Any] | None,
) -> JudgeVerdict:
    structured = llm.with_structured_output(JudgeVerdict)
    result = structured.invoke(
        [
            SystemMessage(content=JUDGE_SYSTEM),
            HumanMessage(
                content=(
                    f"Question:\n{question}\n\n"
                    f"Answer:\n{answer}\n\n"
                    f"SQL:\n{sql or '(none)'}\n\n"
                    f"Query result:\n{query_result or '(none)'}\n\n"
                    f"Python/stats result:\n{python_result or '(none)'}\n"
                )
            ),
        ]
    )
    if isinstance(result, JudgeVerdict):
        return result
    return JudgeVerdict.model_validate(result)
