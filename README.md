# AI Data Analyst

Production-style autonomous data analyst for the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). **Phases 0–11** are in place (agent + API + Next.js + observability + Docker/AWS).

## Setup

```bash
uv sync --group dev
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

## Docker

```bash
docker compose up --build   # API :8000 + Next.js :3000
```

## AWS

Terraform + CD: [infra/aws/README.md](infra/aws/README.md) and [docs/deploy/README.md](docs/deploy/README.md)

```bash
aws configure
make aws-bootstrap      # ECR + Secrets + GitHub OIDC role
make aws-push-image     # first image to ECR
make aws-app-runner     # App Runner API
```

CD workflow: `.github/workflows/cd-aws.yml` (enable with `AWS_CD_ENABLED=true`).

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | readiness (`auth_required` when `API_KEYS` set) |
| GET | `/api/v1/dataset` | tables |
| POST | `/api/v1/analysis` | `mode: agent \| sql` |
| GET | `/charts/<file>.png` | rendered chart images |

Docs: http://127.0.0.1:8000/docs

### Security

- Optional API keys via `API_KEYS` (`X-API-Key` or Bearer).
- Rate limit: `API_RATE_LIMIT_PER_MINUTE` (default 30).
- Analysis timeout: `API_ANALYSIS_TIMEOUT_SECONDS` (default 180).
- Read-only DuckDB, SQL allowlist, iteration caps, structured stats only.

### Observability

- JSON logs with `request_id` / `run_id`, `X-Request-Id` header.
- Analysis responses include `observability` metrics.

## Architecture (separation of concerns)

| Layer | Package | Responsibility |
| --- | --- | --- |
| HTTP | `api/` | Routes, schemas, DI; thin adapters |
| Application | `api/services/` | Orchestration (mode, timeout, DTO mapping) |
| Agent | `agent/` | LangGraph planning, critic, recovery |
| Analyst | `analyst/` | SQL generate → execute → summarize |
| Tools | `tools/` | SQL, stats, charts (no HTTP) |
| Data | `data/` | DuckDB + ingest/profile |
| Cross-cutting | `security/`, `observability/` | Framework-agnostic policies + metrics |

Dependencies flow **down** only: `api` → `agent`/`analyst` → `tools` → `data`.

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

CI: `.github/workflows/ci.yml`. AWS CD: `.github/workflows/cd-aws.yml`.

## What's next

Phase 12: interview/demo prep.
