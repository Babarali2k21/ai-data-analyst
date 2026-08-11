# Deploying AI Data Analyst

## Local Docker Compose

```bash
cp .env.example .env   # set OPENAI_API_KEY
docker compose up --build
```

- API: http://localhost:8000/docs
- Next.js UI: http://localhost:3000
- Streamlit demo (optional profile):

```bash
docker compose --profile demo up --build streamlit
```

Open http://localhost:8501

The image ships a small fixture DuckDB under `data/demo/` so you do not need the full Kaggle dump inside the container.

## Streamlit Community Cloud (live demo)

Best free public demo path:

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Settings:
   - Repository: your fork
   - Branch: `master`
   - Main file path: `apps/streamlit/app.py`
   - Python requirements file: `requirements-streamlit.txt`
4. **Secrets** (App settings → Secrets), paste:

```toml
OPENAI_API_KEY = "sk-..."
LLM_MODEL = "gpt-4.1-mini"
DEMO_QUERY_LIMIT = 3
```

5. Deploy.

### Token burn protection

- Each visitor gets **3 queries** (`DEMO_QUERY_LIMIT`).
- Quota is keyed by IP + sticky `vid` query param and stored in SQLite.
- Prefer **SQL mode** in the UI for cheaper demos; use agent mode sparingly.

Note: Streamlit Cloud disk is ephemeral across restarts, so quotas reset if the app sleeps/redeploys. That is intentional for a light public demo; raise the limit only if you accept more spend.

## AWS (production-style)

### Option A — App Runner (simplest managed container)

1. Build & push the API image:

```bash
aws ecr create-repository --repository-name ai-data-analyst-api
docker build -t ai-data-analyst-api .
docker tag ai-data-analyst-api:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ai-data-analyst-api:latest
aws ecr get-login-password | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ai-data-analyst-api:latest
```

2. Create an App Runner service from that ECR image.
3. Set env vars: `OPENAI_API_KEY`, `DUCKDB_PATH=/app/data/demo/analytics.duckdb`, `DEMO_QUERY_LIMIT=3`, `API_KEYS=...`.
4. Health check path: `/health`.

### Option B — ECS Fargate + ALB

Use the same image as the App Runner task definition, attach an Application Load Balancer, and store secrets in AWS Secrets Manager / SSM Parameter Store. Mount an EFS volume only if you need durable chart/quota state.

### Frontend on AWS

- Build `apps/web` with `NEXT_PUBLIC_API_BASE_URL` pointing at the App Runner/ALB URL.
- Host on Amplify, S3+CloudFront, or a second App Runner service from `apps/web/Dockerfile`.

### Recommended interview demo split

| Surface | Use |
| --- | --- |
| Streamlit Cloud | Public link for recruiters (3-query cap) |
| Docker Compose locally | Full API + Next.js walkthrough |
| AWS App Runner | Optional “I deployed it” talking point |
