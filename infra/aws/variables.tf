variable "aws_region" {
  type        = string
  description = "AWS region for ECR and App Runner."
  default     = "eu-central-1"
}

variable "project_name" {
  type        = string
  description = "Name prefix for resources."
  default     = "ai-data-analyst"
}

variable "github_org_repo" {
  type        = string
  description = "GitHub repo allowed to assume the deploy role (org/name)."
  default     = "Babarali2k21/ai-data-analyst"
}

variable "github_branch" {
  type        = string
  description = "Branch allowed for OIDC assume-role."
  default     = "master"
}

variable "openai_api_key" {
  type        = string
  description = "OpenAI API key stored in Secrets Manager and injected into App Runner."
  sensitive   = true
}

variable "demo_query_limit" {
  type        = string
  description = "Per-visitor demo query cap."
  default     = "3"
}

variable "api_keys" {
  type        = string
  description = "Optional comma-separated API keys for the FastAPI service. Empty disables auth."
  default     = ""
  sensitive   = true
}

variable "create_app_runner" {
  type        = bool
  description = "Create App Runner service. Set false for ECR+IAM only until an image exists."
  default     = false
}

variable "github_oidc_provider_arn" {
  type        = string
  description = "Existing GitHub OIDC provider ARN (account-wide). Leave empty to create one."
  default     = ""
}

variable "image_tag" {
  type        = string
  description = "ECR image tag for App Runner (use after first CD push)."
  default     = "latest"
}

variable "cpu" {
  type        = string
  description = "App Runner CPU units."
  default     = "1024"
}

variable "memory" {
  type        = string
  description = "App Runner memory (MB)."
  default     = "2048"
}
