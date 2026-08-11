"""Application settings loaded from environment / .env."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root: src/ai_data_analyst/config.py -> parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration for data layer and (later) the agent."""

    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    # gpt-4.1-mini: strong SQL/coding, Chat Completions compatible, low eval cost
    llm_model: str = "gpt-4.1-mini"
    llm_temperature: float = 0.0

    duckdb_path: Path = Field(default=_REPO_ROOT / "data" / "processed" / "analytics.duckdb")
    olist_raw_dir: Path = Field(default=_REPO_ROOT / "data" / "raw" / "olist")
    olist_metadata_dir: Path = Field(default=_REPO_ROOT / "datasets" / "olist")
    sql_row_limit: int = 200
    stats_row_limit: int = 5000
    max_agent_iterations: int = 3
    charts_dir: Path = Field(default=_REPO_ROOT / "data" / "processed" / "charts")

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False
    api_cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://localhost:5173",
        ]
    )

    # Phase 10 — security + observability
    log_level: str = "INFO"
    api_keys: list[str] = Field(default_factory=list)
    api_rate_limit_per_minute: int = 30
    api_analysis_timeout_seconds: float = 180.0

    # Bundled lightweight DuckDB for Docker / AWS (fixture subset)
    demo_duckdb_path: Path = Field(
        default=_REPO_ROOT / "data" / "demo" / "analytics.duckdb"
    )

    @field_validator("api_keys", mode="before")
    @classmethod
    def _split_api_keys(cls, value: object) -> object:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value

    @field_validator(
        "duckdb_path",
        "olist_raw_dir",
        "olist_metadata_dir",
        "charts_dir",
        "demo_duckdb_path",
        mode="after",
    )
    @classmethod
    def _resolve_relative_paths(cls, value: Path) -> Path:
        if not value.is_absolute():
            return (_REPO_ROOT / value).resolve()
        return value

    @property
    def repo_root(self) -> Path:
        return _REPO_ROOT


@lru_cache
def get_settings() -> Settings:
    return Settings()
