"""Benchmark runner for sql and agent modes."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from ai_data_analyst.agent.graph import run_analyst_agent
from ai_data_analyst.analyst.sql_pipeline import ask_sql
from ai_data_analyst.config import Settings, get_settings
from ai_data_analyst.evaluation.judge import judge_answer
from ai_data_analyst.evaluation.loader import default_benchmark_path, load_benchmark
from ai_data_analyst.evaluation.metrics import (
    numbers_supported_by_result,
    score_answer,
    score_contains,
    score_numeric,
)
from ai_data_analyst.evaluation.models import (
    BenchmarkQuestion,
    EvalMode,
    EvalSummary,
    QuestionResult,
)
from ai_data_analyst.llm.client import get_chat_model


def _tool_correct(expected: str, selected: str | None) -> bool | None:
    if selected is None:
        return None
    if expected == "either":
        return selected in {"sql", "python"}
    return selected == expected


def evaluate_question(
    item: BenchmarkQuestion,
    *,
    mode: EvalMode,
    settings: Settings,
    llm: BaseChatModel | None = None,
    use_judge: bool = True,
) -> QuestionResult:
    started = time.perf_counter()
    try:
        answer = ""
        sql: str | None = None
        query_result: dict[str, Any] = {}
        python_result: dict[str, Any] = {}
        tool_selected: str | None = None
        critic_passed: bool | None = None
        iterations = 0
        charts = 0
        sql_executed = False

        if mode == "sql":
            result = ask_sql(item.question, settings=settings, llm=llm)
            answer = result.answer
            sql = result.sql
            query_result = result.query_result.model_dump()
            python_result = {}
            tool_selected = "sql"
            critic_passed = None
            iterations = result.attempts
            charts = 0
            sql_executed = True
        else:
            agent = run_analyst_agent(item.question, settings=settings, llm=llm)
            answer = agent.answer
            sql = agent.sql
            query_result = agent.query_result
            python_result = agent.python_result
            tool_selected = str((agent.plan or {}).get("tool") or "") or None
            critic_passed = agent.critic_passed
            iterations = agent.iteration
            charts = len(agent.charts)
            sql_executed = bool(sql) and not (
                agent.failure_type == "tool_error" and not answer
            )

        latency_ms = (time.perf_counter() - started) * 1000

        numeric_correct = None
        if item.gold_numeric is not None:
            numeric_correct = score_numeric(answer, item.gold_numeric, item.numeric_tolerance)

        contains_correct = None
        if item.gold_contains:
            contains_correct = score_contains(answer, item.gold_contains)

        judge_correct = None
        hallucinated = numbers_supported_by_result(answer, query_result, python_result)
        if use_judge and item.require_judge:
            judge_llm = llm or get_chat_model(settings)
            verdict = judge_answer(
                judge_llm,
                question=item.question,
                answer=answer,
                sql=sql,
                query_result=query_result,
                python_result=python_result,
            )
            judge_correct = verdict.correct
            if verdict.hallucinated:
                hallucinated = True

        answer_correct = score_answer(item, answer, judge_correct=judge_correct)
        success = bool(answer.strip()) and (critic_passed is not False if mode == "agent" else True)

        return QuestionResult(
            id=item.id,
            question=item.question,
            difficulty=item.difficulty,
            category=item.category,
            mode=mode,
            success=success,
            sql_executed=sql_executed,
            tool_selected=tool_selected or None,
            tool_correct=_tool_correct(item.expected_tool, tool_selected),
            answer=answer,
            sql=sql,
            numeric_correct=numeric_correct,
            contains_correct=contains_correct,
            judge_correct=judge_correct,
            answer_correct=answer_correct,
            hallucinated=hallucinated,
            critic_passed=critic_passed,
            iterations=iterations,
            latency_ms=latency_ms,
            charts=charts,
        )
    except Exception as exc:  # noqa: BLE001
        latency_ms = (time.perf_counter() - started) * 1000
        return QuestionResult(
            id=item.id,
            question=item.question,
            difficulty=item.difficulty,
            category=item.category,
            mode=mode,
            success=False,
            sql_executed=False,
            error=str(exc),
            latency_ms=latency_ms,
        )


def summarize(results: list[QuestionResult], *, suite: str, mode: EvalMode) -> EvalSummary:
    n = len(results) or 1
    completed = sum(1 for r in results if r.success)
    sql_ok = sum(1 for r in results if r.sql_executed)
    tool_scores = [r.tool_correct for r in results if r.tool_correct is not None]
    answer_scores = [r.answer_correct for r in results if r.answer_correct is not None]
    halluc = [r.hallucinated for r in results if r.hallucinated is not None]

    return EvalSummary(
        suite=suite,
        mode=mode,
        n_questions=len(results),
        task_completion_rate=completed / n,
        sql_execution_accuracy=sql_ok / n,
        tool_selection_accuracy=(sum(bool(x) for x in tool_scores) / len(tool_scores))
        if tool_scores
        else None,
        answer_accuracy=(sum(bool(x) for x in answer_scores) / len(answer_scores))
        if answer_scores
        else None,
        hallucination_rate=(sum(bool(x) for x in halluc) / len(halluc)) if halluc else None,
        avg_iterations=sum(r.iterations for r in results) / n,
        avg_latency_ms=sum(r.latency_ms for r in results) / n,
        results=results,
    )


def run_eval(
    *,
    mode: EvalMode = "agent",
    path: Path | None = None,
    limit: int | None = None,
    ids: list[str] | None = None,
    difficulty: str | None = None,
    use_judge: bool = True,
    settings: Settings | None = None,
    llm: BaseChatModel | None = None,
) -> EvalSummary:
    settings = settings or get_settings()
    suite = load_benchmark(path)
    questions = suite.questions
    if ids:
        id_set = set(ids)
        questions = [q for q in questions if q.id in id_set]
    if difficulty:
        questions = [q for q in questions if q.difficulty == difficulty]
    if limit is not None:
        questions = questions[:limit]

    results = [
        evaluate_question(
            q,
            mode=mode,
            settings=settings,
            llm=llm,
            use_judge=use_judge,
        )
        for q in questions
    ]
    return summarize(results, suite=suite.name, mode=mode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Olist analyst evaluation suite")
    parser.add_argument("--mode", choices=["sql", "agent"], default="agent")
    parser.add_argument("--benchmark", type=Path, default=None, help="Path to benchmark YAML")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--ids", nargs="*", default=None)
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], default=None)
    parser.add_argument("--no-judge", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write JSON report (default: data/processed/eval_<mode>.json)",
    )
    args = parser.parse_args()

    settings = get_settings()
    output = args.output
    if output is None:
        output = settings.repo_root / "data" / "processed" / f"eval_{args.mode}.json"

    summary = run_eval(
        mode=args.mode,
        path=args.benchmark or default_benchmark_path(),
        limit=args.limit,
        ids=args.ids,
        difficulty=args.difficulty,
        use_judge=not args.no_judge,
        settings=settings,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(summary.model_dump_json(indent=2) + "\n", encoding="utf-8")

    print(f"Suite: {summary.suite} | mode={summary.mode} | n={summary.n_questions}")
    print(f"Task completion:     {summary.task_completion_rate:.1%}")
    print(f"SQL execution:       {summary.sql_execution_accuracy:.1%}")
    if summary.tool_selection_accuracy is not None:
        print(f"Tool selection:      {summary.tool_selection_accuracy:.1%}")
    if summary.answer_accuracy is not None:
        print(f"Answer accuracy:     {summary.answer_accuracy:.1%}")
    if summary.hallucination_rate is not None:
        print(f"Hallucination rate:  {summary.hallucination_rate:.1%}")
    print(f"Avg iterations:      {summary.avg_iterations:.2f}")
    print(f"Avg latency ms:      {summary.avg_latency_ms:.0f}")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
