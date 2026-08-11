output "aws_account_id" {
  value = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  value = data.aws_region.current.name
}

output "ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "ecr_repository_name" {
  value = aws_ecr_repository.api.name
}

output "github_actions_role_arn" {
  value       = aws_iam_role.github_actions.arn
  description = "Set as GitHub Actions secret AWS_ROLE_ARN"
}

output "openai_secret_arn" {
  value = aws_secretsmanager_secret.openai.arn
}

output "app_runner_service_arn" {
  value       = try(aws_apprunner_service.api[0].arn, null)
  description = "Set as GitHub Actions variable APP_RUNNER_SERVICE_ARN (after create_app_runner=true)"
}

output "app_runner_service_url" {
  value       = try(aws_apprunner_service.api[0].service_url, null)
  description = "HTTPS URL for the API (after App Runner is created)"
}

output "github_actions_variables" {
  description = "Values to paste into GitHub Actions variables/secrets"
  value = {
    AWS_CD_ENABLED         = "true"
    AWS_REGION             = data.aws_region.current.name
    ECR_REPOSITORY         = aws_ecr_repository.api.name
    AWS_AUTH_MODE          = "oidc"
    APP_RUNNER_SERVICE_ARN = try(aws_apprunner_service.api[0].arn, "<run apply with create_app_runner=true after first image push>")
    AWS_ROLE_ARN           = aws_iam_role.github_actions.arn
  }
}
