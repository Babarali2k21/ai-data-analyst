# AI Data Analyst

Production-style autonomous data analyst agent for the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). **Phases 0–5** are in place: setup, DuckDB, LLM→SQL, LangGraph agent, Python/stats tools, and critic + structured error recovery.

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

Flow: **Planner → Router → SQL/Python analyst → Critic → retry/replan/finalize**.

Phase 5 recovery:
- Rule-based checks for tool/schema/empty failures
- LLM critic with `failure_type` + `recovery_action`
- Direct `retry_sql` / `retry_python` without full replan
- Tool switches (`switch_to_sql` / `switch_to_python`) and replan loops
- Iteration / retry caps to avoid infinite loops

Python analyst: SQL fetch → fixed stats op → NL findings (no arbitrary code execution).

## Phase 2 single-shot SQL

```bash
uv run ask-sql "How many orders were delivered?"
```

## Development

```bash
make lint && make typecheck && make test
```

## What's next

Phase 6+: visualization, evaluation, FastAPI, Next.js UI, observability/security, deploy.
