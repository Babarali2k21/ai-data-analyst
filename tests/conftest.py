from pathlib import Path

import pytest

from ai_data_analyst.api.deps import reset_rate_limiter
from ai_data_analyst.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_OLIST = REPO_ROOT / "tests" / "fixtures" / "olist"
METADATA_DIR = REPO_ROOT / "datasets" / "olist"


@pytest.fixture(autouse=True)
def _reset_api_rate_limiter() -> object:
    reset_rate_limiter()
    yield
    reset_rate_limiter()


@pytest.fixture
def metadata_dir() -> Path:
    return METADATA_DIR


@pytest.fixture
def fixture_raw_dir() -> Path:
    return FIXTURES_OLIST


@pytest.fixture
def temp_settings(tmp_path: Path, fixture_raw_dir: Path, metadata_dir: Path) -> Settings:
    return Settings(
        duckdb_path=tmp_path / "test.duckdb",
        olist_raw_dir=fixture_raw_dir,
        olist_metadata_dir=metadata_dir,
        charts_dir=tmp_path / "charts",
        openai_api_key="",
        llm_model="gpt-4.1-mini",
    )
