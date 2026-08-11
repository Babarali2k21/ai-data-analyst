# Deploying AI Data Analyst

## Local Docker Compose

```bash
cp .env.example .env   # set OPENAI_API_KEY
docker compose up --build
```

- API: http://localhost:8000/docs
- Next.js UI: http://localhost:3000

The image ships a small fixture DuckDB under `data/demo/` so you do not need the full Kaggle dump inside the container.

## Local development (without Docker)

```bash
make api   # :8000
make web   # :3000
```

## Configuration

See [`.env.example`](../../.env.example). Important knobs:

- `OPENAI_API_KEY` — required for analysis
- `API_KEYS` — optional shared keys for the HTTP API
- `API_RATE_LIMIT_PER_MINUTE` / `API_ANALYSIS_TIMEOUT_SECONDS`
- `DUCKDB_PATH` — defaults to processed analytics DB; Docker uses `data/demo/`

## CI

GitHub Actions runs lint, typecheck, tests, and a Next.js build on every push/PR (`.github/workflows/ci.yml`).
