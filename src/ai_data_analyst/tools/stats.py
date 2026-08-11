"""Deterministic statistical analysis helpers (no arbitrary code execution)."""

from __future__ import annotations

from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, Field

StatOp = Literal[
    "describe",
    "correlation",
    "pct_change",
    "rolling_mean",
    "outliers",
    "group_compare",
]


class StatsSpec(BaseModel):
    """Structured stats request produced by the Python analyst LLM."""

    operation: StatOp
    data_sql: str = Field(description="Read-only SQL that returns the working dataset")
    columns: list[str] = Field(
        default_factory=list,
        description="Numeric columns involved (1+ depending on operation)",
    )
    group_column: str | None = Field(
        default=None,
        description="Categorical column for group_compare",
    )
    window: int = Field(default=3, ge=2, description="Window size for rolling_mean")
    periods: int = Field(default=1, ge=1, description="Lag for pct_change")
    rationale: str = ""


class StatsResult(BaseModel):
    operation: StatOp
    summary: dict[str, Any]
    preview_rows: list[dict[str, Any]] = Field(default_factory=list)


def _require_columns(df: pd.DataFrame, columns: list[str]) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in dataset: {missing}. Have: {list(df.columns)}")


def _numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    _require_columns(df, [column])
    series = pd.to_numeric(df[column], errors="coerce")
    if series.notna().sum() == 0:
        raise ValueError(f"Column {column!r} has no numeric values")
    return series


def describe(df: pd.DataFrame, column: str) -> dict[str, Any]:
    series = _numeric_series(df, column).dropna()
    return {
        "column": column,
        "count": int(series.count()),
        "mean": float(series.mean()),
        "median": float(series.median()),
        "std": float(series.std(ddof=1)) if len(series) > 1 else 0.0,
        "min": float(series.min()),
        "max": float(series.max()),
    }


def correlation(df: pd.DataFrame, columns: list[str]) -> dict[str, Any]:
    if len(columns) < 2:
        raise ValueError("correlation requires at least two columns")
    _require_columns(df, columns)
    numeric = df[columns].apply(pd.to_numeric, errors="coerce")
    corr = numeric.corr(numeric_only=True)
    # Pairwise matrix as nested dict with None for NaN
    matrix: dict[str, dict[str, float | None]] = {}
    for row in corr.index.astype(str):
        matrix[row] = {}
        for col in corr.columns.astype(str):
            value = corr.loc[row, col]
            matrix[row][col] = None if pd.isna(value) else float(value)
    return {"columns": columns, "matrix": matrix}


def pct_change(df: pd.DataFrame, column: str, periods: int = 1) -> dict[str, Any]:
    series = _numeric_series(df, column)
    changed = series.pct_change(periods=periods).dropna()
    if changed.empty:
        return {"column": column, "periods": periods, "count": 0}
    return {
        "column": column,
        "periods": periods,
        "count": int(changed.count()),
        "mean_pct_change": float(changed.mean()),
        "median_pct_change": float(changed.median()),
        "min_pct_change": float(changed.min()),
        "max_pct_change": float(changed.max()),
    }


def rolling_mean(df: pd.DataFrame, column: str, window: int = 3) -> dict[str, Any]:
    series = _numeric_series(df, column)
    rolled = series.rolling(window=window, min_periods=1).mean()
    preview = [
        {"index": str(i), "value": None if pd.isna(v) else float(v)}
        for i, v in list(rolled.items())[-20:]
    ]
    return {
        "column": column,
        "window": window,
        "last_rolling_mean": None if pd.isna(rolled.iloc[-1]) else float(rolled.iloc[-1]),
        "preview": preview,
    }


def outliers_iqr(df: pd.DataFrame, column: str) -> dict[str, Any]:
    series = _numeric_series(df, column).dropna()
    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    mask = (series < lower) | (series > upper)
    outlier_vals = series[mask]
    return {
        "column": column,
        "q1": q1,
        "q3": q3,
        "iqr": float(iqr),
        "lower_bound": float(lower),
        "upper_bound": float(upper),
        "outlier_count": int(mask.sum()),
        "outlier_rate": float(mask.mean()) if len(series) else 0.0,
        "example_outliers": [float(v) for v in outlier_vals.head(10).tolist()],
    }


def group_compare(df: pd.DataFrame, group_column: str, value_column: str) -> dict[str, Any]:
    _require_columns(df, [group_column, value_column])
    work = df[[group_column, value_column]].copy()
    work[value_column] = pd.to_numeric(work[value_column], errors="coerce")
    work = work.dropna(subset=[value_column])
    if work.empty:
        raise ValueError("No numeric values available for group comparison")

    grouped = work.groupby(group_column, dropna=False)[value_column]
    rows: list[dict[str, Any]] = []
    for name, series in grouped:
        rows.append(
            {
                "group": None if pd.isna(name) else str(name),
                "count": int(series.count()),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "std": float(series.std(ddof=1)) if len(series) > 1 else 0.0,
            }
        )
    rows.sort(key=lambda r: r["mean"], reverse=True)
    return {
        "group_column": group_column,
        "value_column": value_column,
        "groups": rows[:50],
        "group_count": len(rows),
    }


def run_stats(df: pd.DataFrame, spec: StatsSpec) -> StatsResult:
    """Execute a StatsSpec against a DataFrame."""
    op = spec.operation
    if op == "describe":
        if not spec.columns:
            raise ValueError("describe requires columns=[value_col]")
        summary = describe(df, spec.columns[0])
    elif op == "correlation":
        cols = spec.columns if len(spec.columns) >= 2 else list(df.columns[:2])
        summary = correlation(df, cols)
    elif op == "pct_change":
        if not spec.columns:
            raise ValueError("pct_change requires columns=[value_col]")
        summary = pct_change(df, spec.columns[0], periods=spec.periods)
    elif op == "rolling_mean":
        if not spec.columns:
            raise ValueError("rolling_mean requires columns=[value_col]")
        summary = rolling_mean(df, spec.columns[0], window=spec.window)
    elif op == "outliers":
        if not spec.columns:
            raise ValueError("outliers requires columns=[value_col]")
        summary = outliers_iqr(df, spec.columns[0])
    elif op == "group_compare":
        if not spec.group_column or not spec.columns:
            raise ValueError("group_compare requires group_column and columns=[value_col]")
        summary = group_compare(df, spec.group_column, spec.columns[0])
    else:
        raise ValueError(f"Unsupported operation: {op}")

    preview = df.head(5).where(pd.notnull(df.head(5)), None).to_dict(orient="records")
    normalized = [{str(k): _jsonable(v) for k, v in row.items()} for row in preview]
    return StatsResult(operation=op, summary=summary, preview_rows=normalized)


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
