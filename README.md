# AI Data Analyst

Production-style autonomous data analyst agent for the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). **Phases 0–4** are in place: setup, DuckDB, LLM→SQL, LangGraph agent, and Python/statistical tools.

## Stack

| Component     | Technology                         |
| ------------- | ---------------------------------- |
| Language      | Python 3.12                        |
| Package mgr   | uv                                 |
| Analytical DB | DuckDB                             |
| LLM           | OpenAI (`gpt-4.1-mini` default)    |
| Agent         | LangGraph                          |
| Stats         | Pandas (structured ops only)       |
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
uv run ask-agent "How many orders were delivered?"
uv run ask-agent "What is the correlation between item price and freight_value?"
```

Flow: **Planner → Router → SQL or Python analyst → Critic → Finalizer** (replan on failure, max 3 iterations).

Python analyst: SQL fetch → fixed stats op (`describe`, `correlation`, `pct_change`, `rolling_mean`, `outliers`, `group_compare`) → NL findings. No arbitrary code execution.

## Phase 2 single-shot SQL

```bash
uv run ask-sql "How many orders were delivered?"
```

## Development

```bash
make lint && make typecheck && make test
```

## What's next

Phase 5+: richer critic recovery, visualization, evaluation, FastAPI, Next.js UI.
