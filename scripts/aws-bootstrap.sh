#!/usr/bin/env bash
# Bootstrap AWS: configure CLI, terraform apply (ECR + IAM + secrets), print GitHub CD settings.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AWS_DIR="$ROOT/infra/aws"

die() { echo "ERROR: $*" >&2; exit 1; }

need() { command -v "$1" >/dev/null 2>&1 || die "Missing '$1'. Install it first."; }

need aws
need terraform

echo "==> Checking AWS credentials"
aws sts get-caller-identity >/dev/null || die "Run: aws configure   (need Access Key + Secret + region)"

ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
REGION="$(aws configure get region || true)"
REGION="${REGION:-eu-central-1}"
echo "    Account: $ACCOUNT"
echo "    Region:  $REGION"

if [[ ! -f "$AWS_DIR/terraform.tfvars" ]]; then
  echo "==> Creating terraform.tfvars from example"
  cp "$AWS_DIR/terraform.tfvars.example" "$AWS_DIR/terraform.tfvars"
  echo "    Edit $AWS_DIR/terraform.tfvars if needed"
fi

if [[ -z "${TF_VAR_openai_api_key:-}" ]]; then
  if [[ -f "$ROOT/.env" ]]; then
    # shellcheck disable=SC1091
    set -a
    # Only pull OPENAI_API_KEY without sourcing the whole file blindly
    KEY_LINE="$(grep -E '^OPENAI_API_KEY=' "$ROOT/.env" | tail -n1 || true)"
    if [[ -n "$KEY_LINE" ]]; then
      export TF_VAR_openai_api_key="${KEY_LINE#OPENAI_API_KEY=}"
    fi
    set +a
  fi
fi

[[ -n "${TF_VAR_openai_api_key:-}" ]] || die "Set OPENAI_API_KEY in .env or export TF_VAR_openai_api_key=sk-..."

cd "$AWS_DIR"
echo "==> terraform init"
terraform init -input=false

echo "==> terraform apply (ECR + OIDC role + Secrets; App Runner deferred)"
terraform apply -input=false -auto-approve \
  -var="aws_region=$REGION" \
  -var="create_app_runner=false"

echo
echo "==> Next steps"
echo "1. Copy GitHub settings from terraform output:"
terraform output -json github_actions_variables | python3 -m json.tool
echo
echo "2. Add GitHub secret AWS_ROLE_ARN and variables AWS_CD_ENABLED=true, AWS_REGION, ECR_REPOSITORY"
echo "3. Push an image (Actions → CD AWS → Run workflow) OR:"
echo "     make aws-push-image"
echo "4. Enable App Runner:"
echo "     cd infra/aws && terraform apply -var='create_app_runner=true' -auto-approve"
echo "5. Set GitHub variable APP_RUNNER_SERVICE_ARN from:"
echo "     terraform output app_runner_service_arn"
