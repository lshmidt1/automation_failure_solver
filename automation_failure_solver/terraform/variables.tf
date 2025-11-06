variable "lambda_region" {
  description = "The AWS region where the Lambda functions will be deployed"
  type        = string
  default     = "us-east-1"
}

variable "lambda_memory_size" {
  description = "The amount of memory allocated to the Lambda functions"
  type        = number
  default     = 128
}

variable "lambda_timeout" {
  description = "The timeout for the Lambda functions in seconds"
  type        = number
  default     = 30
}

variable "sqs_queue_name" {
  description = "The name of the SQS queue for analyzing failures"
  type        = string
}

variable "api_gateway_stage" {
  description = "The stage name for the API Gateway"
  type        = string
  default     = "dev"
}