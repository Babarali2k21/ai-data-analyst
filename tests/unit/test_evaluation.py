from ai_data_analyst.evaluation.loader import load_benchmark
from ai_data_analyst.evaluation.metrics import (
    extract_numbers,
    score_answer,
    score_contains,
    score_numeric,
)
from ai_data_analyst.evaluation.models import BenchmarkQuestion, QuestionResult
from ai_data_analyst.evaluation.runner import summarize


def test_benchmark_has_fifty_questions() -> None:
    suite = load_benchmark()
    assert suite.name == "olist_v1"
    assert len(suite.questions) == 50
    difficulties = {q.difficulty for q in suite.questions}
    assert difficulties == {"easy", "medium", "hard"}


def test_score_numeric_and_contains() -> None:
    assert score_numeric("There are 99,441 orders.", 99441, 0) is True
    assert score_numeric("About 100 orders", 99441, 0) is False
    assert score_contains("Top category is health_beauty", ["health_beauty"]) is True
    assert extract_numbers("mean=120.65, std=2") == [120.65, 2.0]


def test_score_answer_combines_checks() -> None:
    q = BenchmarkQuestion(
        id="t",
        question="q",
        difficulty="easy",
        category="counts",
        gold_numeric=10,
        gold_contains=["orders"],
    )
    assert score_answer(q, "There are 10 orders") is True
    assert score_answer(q, "There are 10 items") is False


def test_summarize_metrics() -> None:
    results = [
        QuestionResult(
            id="a",
            question="q",
            difficulty="easy",
            category="counts",
            mode="agent",
            success=True,
            sql_executed=True,
            tool_selected="sql",
            tool_correct=True,
            answer_correct=True,
            hallucinated=False,
            iterations=1,
            latency_ms=100,
        ),
        QuestionResult(
            id="b",
            question="q2",
            difficulty="hard",
            category="stats",
            mode="agent",
            success=False,
            sql_executed=False,
            tool_selected="python",
            tool_correct=False,
            answer_correct=False,
            hallucinated=True,
            iterations=2,
            latency_ms=200,
        ),
    ]
    summary = summarize(results, suite="olist_v1", mode="agent")
    assert summary.n_questions == 2
    assert summary.task_completion_rate == 0.5
    assert summary.sql_execution_accuracy == 0.5
    assert summary.tool_selection_accuracy == 0.5
    assert summary.answer_accuracy == 0.5
    assert summary.hallucination_rate == 0.5
    assert summary.avg_iterations == 1.5
