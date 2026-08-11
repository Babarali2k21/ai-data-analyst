# AI Data Analyst

Production-style autonomous data analyst agent for the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). **Phases 0–6** are in place: setup, DuckDB, LLM→SQL, LangGraph agent, Python/stats, critic recovery, and structured visualization.

## Stack

| Component     | Technology                         |
| ------------- | ---------------------------------- |
| Language      | Python 3.12                        |
| Package mgr   | uv                                 |
| Analytical DB | DuckDB                             |
| LLM           | OpenAI (`gpt-4.1-mini` default)    |
| Agent         | LangGraph                          |
| Stats         | Pandas (structured ops only)       |
| Charts        | Structured `ChartSpec` + matplotlib|
| Validation    | Pydantic                           |
| Tests         | Pytest                             |

## Setup

```bash
uv sync --all-groups
cp .env.example .env   # set OPENAI_API_KEY; LLM_MODEL=gpt-4.1-mini
make ingest && make profile
```

## Ask via LangGraph agent

```bash
uv run ask-agent "What are the top 5 product categories by revenue?"
uv run ask-agent "What is the correlation between item price and freight_value?"
```

Flow: **Planner → Router → SQL/Python → Critic → Visualizer → Finalizer**.

Charts are structured JSON (not frontend code), e.g.:

```json
{"type": "bar", "x": "category", "y": "revenue", "title": "Top categories"}
```

Optional PNG renders land in `data/processed/charts/`.

## Development

```bash
make lint && make typecheck && make test
```

## What's next

Phase 7+: evaluation framework, FastAPI, Next.js UI, observability/security, deploy.
