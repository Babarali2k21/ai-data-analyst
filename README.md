# AI Data Analyst

Production-style autonomous data analyst agent for the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). The agent plans analyses, runs SQL (and later Python/statistics), validates results, and returns findings (LangGraph + DuckDB). **Phases 0–2** are in place: engineering setup, DuckDB analytics DB, and a basic LLM → SQL analyst.

## Stack

| Component     | Technology                         |
| ------------- | ---------------------------------- |
| Language      | Python 3.12                        |
| Package mgr   | uv                                 |
| Analytical DB | DuckDB                             |
| LLM           | OpenAI (`gpt-4.1-mini` default)    |
| Validation    | Pydantic                           |
| Tests         | Pytest                             |
| Agent (later) | LangGraph                          |
| API (later)   | FastAPI                            |
| UI (later)    | Next.js                            |

**Model choice:** `gpt-4.1-mini` — strong at SQL/coding, Chat Completions compatible, and cheap enough for eval loops. Prefer this over `gpt-5` for Phase 2 (gpt-5 needs the Responses API and burns reasoning tokens).

## Setup

```bash
uv sync --all-groups
cp .env.example .env   # set OPENAI_API_KEY; LLM_MODEL=gpt-4.1-mini
# Place Olist CSVs under data/raw/olist/
make ingest && make profile
```

## Ask a question (Phase 2)

```bash
uv run ask-sql "How many orders were delivered?"
# or
make ask Q='What are the top 5 product categories by revenue?'
```

Pipeline: question → schema-aware SQL generation → read-only validation → DuckDB execute → short NL answer (one repair attempt on failure).

## Development

```bash
make lint
make typecheck
make test
```

## What's next

Phase 3+: LangGraph planner/router/critic, Python stats tools, evaluation, FastAPI, Next.js UI. Geolocation is skipped in v1 ingest.
