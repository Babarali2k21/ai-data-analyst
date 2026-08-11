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

    fig, ax = plt.subplots(figsize=(8, 4.5))
    if spec.type == "line":
        ax.plot([str(x) for x in xs_raw], _as_float_list(ys_raw), marker="o")
    elif spec.type == "bar":
        ax.bar([str(x) for x in xs_raw], _as_float_list(ys_raw))
    elif spec.type == "scatter":
        ax.scatter(_as_float_list(xs_raw), _as_float_list(ys_raw))
    elif spec.type == "hist":
        values = ys_raw if any(v is not None for v in ys_raw) else xs_raw
        ax.hist(
            _as_float_list(values),
            bins=min(20, max(5, len(xs_raw) // 2 or 5)),
        )
    else:
        ax.bar([str(x) for x in xs_raw], _as_float_list(ys_raw))

    ax.set_title(spec.title)
    ax.set_xlabel(spec.x)
    if spec.y:
        ax.set_ylabel(spec.y)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
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
