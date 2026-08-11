# Deploying AI Data Analyst

## Local Docker Compose

```bash
cp .env.example .env   # set OPENAI_API_KEY
docker compose up --build
```

- API: http://localhost:8000/docs
- Next.js UI: http://localhost:3000

The image ships a small fixture DuckDB under `data/demo/` so you do not need the full Kaggle dump inside the container.

## AWS (production-style)

Terraform details: [infra/aws/README.md](../../infra/aws/README.md)

### Quick path

```bash
brew install awscli
brew tap hashicorp/tap && brew install hashicorp/tap/terraform
aws configure   # Access Key ID, Secret, region (eu-central-1)

make aws-bootstrap          # ECR + Secrets + GitHub OIDC role
# copy terraform output → GitHub secrets/variables
make aws-push-image         # first container image to ECR
make aws-app-runner         # create App Runner service
```

### Continuous deployment (GitHub Actions → ECR → App Runner)

Workflow: [`.github/workflows/cd-aws.yml`](../../.github/workflows/cd-aws.yml).

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

Minimum IAM permissions for the role/user: ECR push + `apprunner:StartDeployment`.

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

### ECS Fargate + ALB (advanced)

Use the same image as the App Runner task definition, attach an Application Load Balancer, and store secrets in AWS Secrets Manager / SSM Parameter Store.

### Frontend on AWS

- Build `apps/web` with `NEXT_PUBLIC_API_BASE_URL` pointing at the App Runner URL.
- Host on Amplify, S3+CloudFront, or a second App Runner service from `apps/web/Dockerfile`.

### Recommended interview demo split

| Surface | Use |
| --- | --- |
| Docker Compose locally | Full API + Next.js walkthrough |
| AWS App Runner + CD | Deployed API talking point |
