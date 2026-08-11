# AI Data Analyst

Production-style autonomous data analyst agent for the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). **Phases 0–8** are in place, including a FastAPI backend.

## Setup

```bash
uv sync --all-groups
cp .env.example .env   # set OPENAI_API_KEY
make ingest && make profile
```

## API (Phase 8)

```bash
make api
# or: uv run serve-api
```

Endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness + DuckDB readiness |
| GET | `/api/v1/dataset` | List loaded tables |
| POST | `/api/v1/analysis` | Run `agent` or `sql` analysis |

Example:

```bash
curl -s http://127.0.0.1:8000/health | jq
curl -s http://127.0.0.1:8000/api/v1/dataset | jq
curl -s http://127.0.0.1:8000/api/v1/analysis \
  -H 'Content-Type: application/json' \
  -d '{"question":"How many orders were delivered?","mode":"agent"}' | jq
```

OpenAPI docs: http://127.0.0.1:8000/docs

## CLI

```bash
uv run ask-agent "What are the top 5 product categories by revenue?"
uv run eval-olist --mode agent --ids e01 e06 --no-judge
```

## Development

```bash
make lint && make typecheck && make test
```

## What's next

Phase 9+: Next.js UI, observability/security, Docker/AWS, interview prep.
