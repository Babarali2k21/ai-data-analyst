import pandas as pd
import pytest

from ai_data_analyst.tools.stats import StatsSpec, run_stats


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "month": [1, 2, 3, 4, 5, 6],
            "revenue": [100.0, 120.0, 110.0, 150.0, 140.0, 160.0],
            "freight": [10.0, 12.0, 11.0, 20.0, 14.0, 16.0],
            "region": ["A", "A", "B", "B", "A", "B"],
        }
    )


def test_describe(sample_df: pd.DataFrame) -> None:
    result = run_stats(
        sample_df,
        StatsSpec(operation="describe", data_sql="SELECT 1", columns=["revenue"]),
    )
    assert result.summary["mean"] == pytest.approx(130.0)
    assert result.summary["median"] == pytest.approx(130.0)


def test_correlation(sample_df: pd.DataFrame) -> None:
    result = run_stats(
        sample_df,
        StatsSpec(
            operation="correlation",
            data_sql="SELECT 1",
            columns=["revenue", "freight"],
        ),
    )
    matrix = result.summary["matrix"]
    assert matrix["revenue"]["revenue"] == pytest.approx(1.0)
    assert matrix["revenue"]["freight"] is not None


def test_pct_change_and_rolling(sample_df: pd.DataFrame) -> None:
    pct = run_stats(
        sample_df,
        StatsSpec(operation="pct_change", data_sql="SELECT 1", columns=["revenue"], periods=1),
    )
    assert pct.summary["count"] == 5
    rolled = run_stats(
        sample_df,
        StatsSpec(operation="rolling_mean", data_sql="SELECT 1", columns=["revenue"], window=3),
    )
    assert rolled.summary["window"] == 3
    assert rolled.summary["last_rolling_mean"] is not None


def test_outliers_and_group_compare(sample_df: pd.DataFrame) -> None:
    outliers = run_stats(
        sample_df,
        StatsSpec(operation="outliers", data_sql="SELECT 1", columns=["freight"]),
    )
    assert "outlier_count" in outliers.summary
    groups = run_stats(
        sample_df,
        StatsSpec(
            operation="group_compare",
            data_sql="SELECT 1",
            columns=["revenue"],
            group_column="region",
        ),
    )
    assert groups.summary["group_count"] == 2
    assert len(groups.summary["groups"]) == 2
