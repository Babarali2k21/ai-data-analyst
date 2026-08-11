# AI Data Analyst

Production-style autonomous data analyst agent for the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). **Phases 0–7** are in place, including a 50-question evaluation benchmark.

## Stack

| Component     | Technology                         |
| ------------- | ---------------------------------- |
| Language      | Python 3.12                        |
| Analytical DB | DuckDB                             |
| LLM           | OpenAI (`gpt-4.1-mini`)            |
| Agent         | LangGraph                          |
| Stats         | Pandas structured ops              |
| Charts        | `ChartSpec` + matplotlib           |
| Evaluation    | Custom metrics + LLM-as-judge      |
| Tests         | Pytest                             |

## Setup

```bash
uv sync --all-groups
cp .env.example .env
make ingest && make profile
```

## Ask

```bash
uv run ask-agent "What are the top 5 product categories by revenue?"
```

## Evaluate (Phase 7)

50-question suite at `datasets/olist/benchmark.yaml` (easy/medium/hard).

```bash
# Smoke a couple of easy numeric questions
uv run eval-olist --mode agent --ids e01 e06 --no-judge

# SQL-only baseline vs full agent
uv run eval-olist --mode sql --difficulty easy --no-judge
uv run eval-olist --mode agent --limit 10

# Full suite (uses LLM judge where marked; costs tokens)
uv run eval-olist --mode agent
```

Reports write to `data/processed/eval_<mode>.json` with:

- task completion rate
- SQL execution accuracy
- tool-selection accuracy
- answer accuracy (numeric / contains / judge)
- hallucination rate (heuristic + judge)
- average iterations / latency

## Development

```bash
make lint && make typecheck && make test
```

## What's next

Phase 8+: FastAPI, Next.js UI, observability/security, Docker/AWS, interview prep.
