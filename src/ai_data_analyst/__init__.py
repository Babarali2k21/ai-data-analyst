"""Autonomous data analyst agent for the Olist e-commerce dataset."""

from ai_data_analyst.config import Settings, get_settings


def main() -> None:
    settings = get_settings()
    duckdb_exists = settings.duckdb_path.exists() and settings.duckdb_path.stat().st_size > 0
    print("ai-data-analyst")
    print(f"  duckdb_path:     {settings.duckdb_path}")
    print(f"  duckdb_ready:    {duckdb_exists}")
    print(f"  olist_raw_dir:   {settings.olist_raw_dir}")
    print(f"  metadata_dir:    {settings.olist_metadata_dir}")
    print(f"  llm_model:       {settings.llm_model}")


__all__ = ["Settings", "get_settings", "main"]
