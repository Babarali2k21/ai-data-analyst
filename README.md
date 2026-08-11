# AI Data Analyst

Production-style autonomous data analyst for the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). **Phases 0–9** are in place (agent + API + Next.js UI).

## Setup

```bash
uv sync --all-groups
cp .env.example .env   # set OPENAI_API_KEY
make ingest && make profile

cd apps/web && npm install && cp .env.local.example .env.local
```

## Run API + UI

```bash
# terminal 1
make api

# terminal 2
make web
# open http://localhost:3000
```

UI flow: **Dataset → Question → Analysis activity → Findings → Charts → Supporting SQL**.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | readiness |
| GET | `/api/v1/dataset` | tables |
| POST | `/api/v1/analysis` | `mode: agent \| sql` |
| GET | `/charts/<file>.png` | rendered chart images |

Docs: http://127.0.0.1:8000/docs

## CLI

```bash
uv run ask-agent "What are the top 5 product categories by revenue?"
uv run eval-olist --mode agent --ids e01 e06 --no-judge
```

## Development

```bash
make lint && make typecheck && make test
cd apps/web && npm run build
```

## What's next

Phase 10+: observability/security, Docker/AWS, interview prep.
