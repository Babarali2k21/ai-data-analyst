# AI Data Analyst

Production-style autonomous data analyst for the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). **Phases 0–10** are in place (agent + API + Next.js UI + observability/security).

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
# open http://localhost:3001  (port 3000 is often taken by Grafana)
```

UI flow: **Dataset → Question → Analysis activity → Findings → Charts → Supporting SQL**.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | readiness (`auth_required` when `API_KEYS` set) |
| GET | `/api/v1/dataset` | tables |
| POST | `/api/v1/analysis` | `mode: agent \| sql` |
| GET | `/charts/<file>.png` | rendered chart images |

Docs: http://127.0.0.1:8000/docs

### Security (Phase 10)

- Optional API keys via `API_KEYS` (comma-separated). Send `X-API-Key` or `Authorization: Bearer <key>`. Empty = auth disabled for local demo.
- In-memory rate limit: `API_RATE_LIMIT_PER_MINUTE` (default 30).
- Analysis timeout: `API_ANALYSIS_TIMEOUT_SECONDS` (default 180).
- Existing guards: read-only DuckDB, SQL allowlist, iteration caps, structured stats only (no arbitrary Python).

### Observability (Phase 10)

- JSON structured logs (`LOG_LEVEL`) with `request_id` / `run_id`.
- `X-Request-Id` response header (echo or generate).
- Analysis responses include `observability` (latency, SQL/LLM call counts, token estimates).
- Optional OpenTelemetry FastAPI instrumentation when `opentelemetry-instrumentation-fastapi` is installed.

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

Phase 11–12: Docker/AWS, interview/demo prep.
