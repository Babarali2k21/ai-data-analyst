# AI Data Analyst

Production-style autonomous data analyst agent for the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). The agent will plan analyses, run SQL and Python/statistics, validate results, and return structured findings (LangGraph + DuckDB). This repo currently covers **Phases 0–1**: engineering setup and an analytical DuckDB database.

## Stack

| Component     | Technology             |
| ------------- | ---------------------- |
| Language      | Python 3.12            |
| Package mgr   | uv                     |
| Analytical DB | DuckDB                 |
| Validation    | Pydantic               |
| Tests         | Pytest                 |
| Agent (later) | LangGraph + OpenAI     |
| API (later)   | FastAPI                |
| UI (later)    | Next.js                |

## Setup

```bash
uv sync --all-groups
cp .env.example .env
# Place Olist CSVs under data/raw/olist/ (already present if you downloaded them)
```

## Ingest + profile

```bash
make ingest    # CSV → data/processed/analytics.duckdb
make profile   # writes datasets/olist/profile.json
```

Quick check:

```bash
uv run ai-data-analyst
uv run python -c "
from ai_data_analyst.data.duckdb import get_connection, list_tables
con = get_connection(read_only=True)
print(list_tables(con))
print(con.execute('''
  SELECT date_trunc('month', order_purchase_timestamp) AS month,
         count(*) AS orders
  FROM orders
  GROUP BY 1 ORDER BY 1 LIMIT 5
''').fetchdf())
"
```

## Development

```bash
make lint
make typecheck
make test
```

## What's next

Phases 2+: LLM → SQL analyst, LangGraph planner/router/critic, Python stats tools, evaluation, FastAPI, Next.js UI. Geolocation is intentionally skipped in v1 ingest (large table, limited early demo value).
