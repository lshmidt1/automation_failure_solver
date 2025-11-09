variable "project" {
  type    = string
  default = "automation_failure_solver"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "slack_webhook_url" {
  type    = string
  default = ""
}

variable "jenkins_url" {
  type    = string
  default = "https://jenkins.crbcloud.com"
}

variable "repo_https_url" {
  type        = string
  description = "Azure DevOps HTTPS clone URL"
}

variable "repo_branch" {
  type    = string
  default = "main"
}

variable "jenkins_user" {
  type    = string
  default = "lshmidt"
}

variable "jenkins_token" {
  type      = string
  sensitive = true
}

variable "azdo_pat" {
  type      = string
  sensitive = true
}