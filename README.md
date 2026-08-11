# AI Data Analyst

Production-style autonomous data analyst agent for the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). **Phases 0–3** are in place: engineering setup, DuckDB analytics DB, LLM → SQL analyst, and a LangGraph agent (planner → router → SQL/Python → critic → finalizer).

## Stack

| Component     | Technology                         |
| ------------- | ---------------------------------- |
| Language      | Python 3.12                        |
| Package mgr   | uv                                 |
| Analytical DB | DuckDB                             |
| LLM           | OpenAI (`gpt-4.1-mini` default)    |
| Agent         | LangGraph                          |
| Validation    | Pydantic                           |
| Tests         | Pytest                             |
| API (later)   | FastAPI                            |
| UI (later)    | Next.js                            |

**Model choice:** `gpt-4.1-mini` — strong at SQL/coding, Chat Completions compatible, cheap for eval loops.

## Setup

```bash
uv sync --all-groups
cp .env.example .env   # set OPENAI_API_KEY; LLM_MODEL=gpt-4.1-mini
make ingest && make profile
```

## Ask via LangGraph agent (Phase 3)

```bash
uv run ask-agent "How many orders were delivered?"
make ask-agent Q='What are the top 5 product categories by revenue?'
```

Flow: **Planner → Router → SQL analyst (Python stub) → Critic → Finalizer**, with replan on critic failure (max 3 iterations). Python stats tools arrive in Phase 4; if the planner picks Python today, the stub forces a SQL replan.

## Phase 2 single-shot SQL

```bash
uv run ask-sql "How many orders were delivered?"
```

## Development

```bash
make lint && make typecheck && make test
```

## What's next

Phase 4+: Python/statistical tools, richer critic recovery, visualization, evaluation, FastAPI, Next.js UI.
