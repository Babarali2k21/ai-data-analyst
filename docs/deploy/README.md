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

1. Build & push the API image (or use GitHub Actions CD below):

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

### Continuous deployment (GitHub Actions → ECR → App Runner)

Workflow: [`.github/workflows/cd-aws.yml`](../.github/workflows/cd-aws.yml).

It is **off by default** so pushes stay green without AWS. Enable it once:

**Repository variables** (Settings → Secrets and variables → Actions → Variables):

| Variable | Example | Purpose |
| --- | --- | --- |
| `AWS_CD_ENABLED` | `true` | Turns the CD job on |
| `AWS_REGION` | `eu-central-1` | AWS region (default `eu-central-1`) |
| `ECR_REPOSITORY` | `ai-data-analyst-api` | ECR repo name |
| `AWS_AUTH_MODE` | `oidc` or `keys` | Auth style (default `oidc`) |
| `APP_RUNNER_SERVICE_ARN` | `arn:aws:apprunner:...:service/...` | Triggers `start-deployment` after push |

**Secrets** (OIDC — recommended, `AWS_AUTH_MODE=oidc` or unset):

| Secret | Purpose |
| --- | --- |
| `AWS_ROLE_ARN` | IAM role for GitHub OIDC (`sts:AssumeRoleWithWebIdentity`) |

**Secrets** (access keys — `AWS_AUTH_MODE=keys`):

| Secret | Purpose |
| --- | --- |
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret |

Minimum IAM permissions for the role/user: `ecr:*` on the repo (or the usual push set), plus `apprunner:StartDeployment` on the service.

OIDC trust (GitHub → AWS) sketch:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com" },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:Babarali2k21/ai-data-analyst:*"
        }
      }
    }
  ]
}
```

After setup, pushes that change the API image (or **Actions → CD AWS → Run workflow**) build, push `:sha` + `:latest`, and redeploy App Runner when `APP_RUNNER_SERVICE_ARN` is set.

If App Runner has **automatic deployments from ECR** enabled, you can leave `APP_RUNNER_SERVICE_ARN` empty and still get CD from the image push alone.

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
| AWS App Runner + CD | Optional “I deployed it” talking point |
