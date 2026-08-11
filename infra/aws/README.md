# AWS infrastructure (Terraform)

Provisions:

- ECR repository (`ai-data-analyst-api`)
- Secrets Manager secret for `OPENAI_API_KEY`
- GitHub Actions OIDC IAM role (for CD)
- App Runner IAM roles
- Optional App Runner service (after the first image exists)

## Prerequisites

```bash
brew install awscli
brew tap hashicorp/tap && brew install hashicorp/tap/terraform
aws configure   # Access Key, Secret, region (e.g. eu-central-1)
```

Put `OPENAI_API_KEY` in the repo `.env` (or export `TF_VAR_openai_api_key`).

## One-command bootstrap

From the repo root:

```bash
make aws-bootstrap
```

This runs `scripts/aws-bootstrap.sh`: Terraform apply with **App Runner off**, then prints the GitHub Actions values to copy.

## Manual steps

```bash
cd infra/aws
cp terraform.tfvars.example terraform.tfvars
export TF_VAR_openai_api_key='sk-...'
terraform init
terraform apply -var='create_app_runner=false'
```

### Wire GitHub CD

From `terraform output`:

| GitHub | Value |
| --- | --- |
| Secret `AWS_ROLE_ARN` | `github_actions_role_arn` |
| Variable `AWS_CD_ENABLED` | `true` |
| Variable `AWS_REGION` | region |
| Variable `ECR_REPOSITORY` | `ecr_repository_name` |
| Variable `AWS_AUTH_MODE` | `oidc` |

### Push the first image

```bash
make aws-push-image
# or: Actions → CD AWS → Run workflow (after enabling CD vars)
```

### Create App Runner

```bash
cd infra/aws
terraform apply -var='create_app_runner=true' -auto-approve
terraform output app_runner_service_url
terraform output app_runner_service_arn   # → GitHub variable APP_RUNNER_SERVICE_ARN
```

API health: `https://<service_url>/health`

## Destroy

```bash
cd infra/aws
terraform destroy
```
