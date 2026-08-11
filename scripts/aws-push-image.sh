#!/usr/bin/env bash
# Build the API image and push it to the Terraform-managed ECR repo.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AWS_DIR="$ROOT/infra/aws"

command -v aws >/dev/null || { echo "Install awscli first"; exit 1; }
command -v docker >/dev/null || { echo "Docker must be running"; exit 1; }
command -v terraform >/dev/null || { echo "Install terraform first"; exit 1; }

cd "$AWS_DIR"
REPO_URL="$(terraform output -raw ecr_repository_url)"
REGION="$(terraform output -raw aws_region)"
ACCOUNT="$(terraform output -raw aws_account_id)"
TAG="${1:-latest}"

echo "==> Logging into ECR $REGION"
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"

echo "==> Building and pushing $REPO_URL:$TAG"
cd "$ROOT"
docker build -t "$REPO_URL:$TAG" -t "$REPO_URL:latest" .
docker push "$REPO_URL:$TAG"
docker push "$REPO_URL:latest"
echo "Pushed $REPO_URL:$TAG"
