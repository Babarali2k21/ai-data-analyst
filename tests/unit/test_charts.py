from pathlib import Path

from ai_data_analyst.tools.chart_render import render_chart_png
from ai_data_analyst.tools.charts import (
    ChartProposal,
    ChartSpec,
    attach_series,
    chart_from_group_compare,
    heuristic_chart_from_rows,
    validate_chart_against_columns,
)


def test_heuristic_bar_chart() -> None:
    rows = [
        {"category": "a", "revenue": 10},
        {"category": "b", "revenue": 20},
    ]
    chart = heuristic_chart_from_rows(rows, title="Revenue by category")
    assert chart is not None
    assert chart.type == "bar"
    assert chart.x == "category"
    assert chart.y == "revenue"


def test_heuristic_line_for_month() -> None:
    rows = [{"month": "2018-01", "orders": 1}, {"month": "2018-02", "orders": 2}]
    chart = heuristic_chart_from_rows(rows)
    assert chart is not None
    assert chart.type == "line"


def test_validate_chart_proposal() -> None:
    proposal = ChartProposal(
        should_chart=True,
        type="bar",
        x="category",
        y="revenue",
        title="Top categories",
    )
    spec = validate_chart_against_columns(proposal, ["category", "revenue"])
    assert spec is not None
    assert spec.title == "Top categories"
    assert validate_chart_against_columns(proposal, ["category"]) is None


def test_attach_series_and_group_compare(tmp_path: Path) -> None:
    rows = [{"category": "a", "revenue": 10}, {"category": "b", "revenue": 20}]
    spec = ChartSpec(type="bar", x="category", y="revenue", title="Rev")
    with_series = attach_series(spec, rows)
    assert len(with_series.series) == 2
    assert with_series.series[0]["x"] == "a"

    group_chart = chart_from_group_compare(
        {
            "group_column": "region",
            "value_column": "revenue",
            "groups": [{"group": "SP", "mean": 10.0}, {"group": "RJ", "mean": 20.0}],
        }
    )
    assert group_chart is not None
    assert group_chart.type == "bar"

    path = render_chart_png(with_series, tmp_path / "rev.png")
    assert path.exists()
    assert path.stat().st_size > 0
