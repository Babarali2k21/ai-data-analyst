"""Optional matplotlib rendering of ChartSpec objects."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_data_analyst.tools.charts import ChartSpec


def render_chart_png(spec: ChartSpec, output_path: Path) -> Path:
    """Render a ChartSpec to a PNG file using matplotlib."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path.parent.mkdir(parents=True, exist_ok=True)
    xs_raw = [p.get("x") for p in spec.series]
    ys_raw = [p.get("y") for p in spec.series]
    labels = [str(x) for x in xs_raw]
    values = _as_float_list(ys_raw)
    n = len(labels)
    long_labels = any(len(label) > 12 for label in labels)
    # Many/long category names overflow on a vertical bar chart — use horizontal.
    use_horizontal_bar = spec.type == "bar" and n > 0 and (n > 8 or long_labels)

    if use_horizontal_bar:
        height = max(4.5, min(18.0, 0.38 * n + 1.8))
        fig, ax = plt.subplots(figsize=(9.5, height))
        # Highest value at the top for ranked "top N" charts.
        ax.barh(labels[::-1], values[::-1])
        ax.set_xlabel(spec.y or "value")
        ax.set_ylabel(spec.x)
    else:
        width = max(8.0, min(16.0, 0.45 * max(n, 1) + 2.0))
        fig, ax = plt.subplots(figsize=(width, 4.8))
        if spec.type == "line":
            ax.plot(labels, values, marker="o")
        elif spec.type == "bar":
            ax.bar(labels, values)
        elif spec.type == "scatter":
            ax.scatter(_as_float_list(xs_raw), values)
        elif spec.type == "hist":
            hist_values = ys_raw if any(v is not None for v in ys_raw) else xs_raw
            ax.hist(
                _as_float_list(hist_values),
                bins=min(20, max(5, n // 2 or 5)),
            )
        else:
            ax.bar(labels, values)
        ax.set_xlabel(spec.x)
        if spec.y:
            ax.set_ylabel(spec.y)
        if n > 4:
            ax.tick_params(axis="x", labelrotation=35, labelsize=8)
            fig.autofmt_xdate(rotation=35, ha="right")

    ax.set_title(spec.title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _as_float_list(values: list[Any]) -> list[float]:
    out: list[float] = []
    for value in values:
        try:
            out.append(float(value))
        except (TypeError, ValueError):
            out.append(0.0)
    return out
