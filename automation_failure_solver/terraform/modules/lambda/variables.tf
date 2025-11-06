variable "lambda_function_name" {
  description = "The name of the Lambda function"
  type        = string
}

variable "lambda_runtime" {
  description = "The runtime environment for the Lambda function"
  type        = string
  default     = "python3.8"
}

variable "lambda_handler" {
  description = "The handler for the Lambda function"
  type        = string
}

variable "lambda_memory_size" {
  description = "The amount of memory available to the function"
  type        = number
  default     = 128
}

variable "lambda_timeout" {
  description = "The function execution time at which Lambda should terminate the function"
  type        = number
  default     = 3
}

variable "environment_variables" {
  description = "Environment variables for the Lambda function"
  type        = map(string)
  default     = {}
}