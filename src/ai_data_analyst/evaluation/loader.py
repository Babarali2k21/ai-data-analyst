"""Load benchmark suites from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from ai_data_analyst.config import get_settings
from ai_data_analyst.evaluation.models import BenchmarkSuite


def default_benchmark_path() -> Path:
    return get_settings().olist_metadata_dir / "benchmark.yaml"


def load_benchmark(path: Path | None = None) -> BenchmarkSuite:
    path = path or default_benchmark_path()
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return BenchmarkSuite.model_validate(data)
