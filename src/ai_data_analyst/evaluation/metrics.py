"""Scoring helpers for benchmark answers."""

from __future__ import annotations

import re
from typing import Any

from ai_data_analyst.evaluation.models import BenchmarkQuestion

_NUMBER_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def extract_numbers(text: str) -> list[float]:
    values: list[float] = []
    for match in _NUMBER_RE.findall(text or ""):
        try:
            values.append(float(match.replace(",", "")))
        except ValueError:
            continue
    return values


def score_numeric(answer: str, expected: float, tolerance: float) -> bool:
    numbers = extract_numbers(answer)
    if not numbers:
        return False
    return any(abs(n - expected) <= tolerance for n in numbers)


def score_contains(answer: str, needles: list[str]) -> bool:
    lower = (answer or "").lower()
    return all(needle.lower() in lower for needle in needles)


def numbers_supported_by_result(
    answer: str,
    query_result: dict[str, Any] | None,
    python_result: dict[str, Any] | None,
    *,
    tolerance: float = 1.0,
) -> bool | None:
    """Heuristic hallucination check: answer numbers appear in tool outputs."""
    answer_nums = extract_numbers(answer)
    if not answer_nums:
        return None

    corpus_nums: list[float] = []
    if query_result:
        for row in query_result.get("rows") or []:
            for value in row.values():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    corpus_nums.append(float(value))
                elif isinstance(value, str):
                    corpus_nums.extend(extract_numbers(value))
    if python_result:
        corpus_nums.extend(extract_numbers(str(python_result.get("summary") or {})))

    if not corpus_nums:
        return None

    def supported(n: float) -> bool:
        return any(abs(n - c) <= max(tolerance, abs(c) * 0.01) for c in corpus_nums)

    # Consider hallucinated if a majority of mentioned numbers are unsupported
    unsupported = sum(1 for n in answer_nums if not supported(n))
    return unsupported > max(1, len(answer_nums) // 2)


def score_answer(
    question: BenchmarkQuestion,
    answer: str,
    *,
    judge_correct: bool | None = None,
) -> bool | None:
    """Combine deterministic checks (+ optional judge) into answer_correct."""
    votes: list[bool] = []
    if question.gold_numeric is not None:
        votes.append(score_numeric(answer, question.gold_numeric, question.numeric_tolerance))
    if question.gold_contains:
        votes.append(score_contains(answer, question.gold_contains))
    if judge_correct is not None:
        votes.append(judge_correct)
    if not votes:
        return None
    return all(votes)
