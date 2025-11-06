terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" { region = var.aws_region }

locals {
  bucket_name   = "${var.project}-s3-${random_id.rand.hex}"
  queue_name    = "${var.project}-queue"
  table_name    = "${var.project}-ddb"
  ingest_name   = "${var.project}-ingest"
  analyze_name  = "${var.project}-analyze"
}

resource "random_id" "rand" { byte_length = 4 }

# S3 לאחסון לוגים/דו\"חות
resource "aws_s3_bucket" "logs" {
  bucket        = local.bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "v" {
  bucket = aws_s3_bucket.logs.id
  versioning_configuration { status = "Enabled" }
}

# SQS לתור ניתוח
resource "aws_sqs_queue" "analyze" {
  name                      = local.queue_name
  visibility_timeout_seconds = 180
}

# DynamoDB לתוצאות
resource "aws_dynamodb_table" "results" {
  name         = local.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"
  attribute { name = "pk" type = "S" }
  attribute { name = "sk" type = "S" }
}

# IAM policy משותף ללמבדה
data "aws_iam_policy_document" "lambda_base" {
  statement {
    sid     = "Logs"
    actions = ["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

# Ingest Lambda — כתיבה ל-S3, שליחה ל-SQS
data "aws_iam_policy_document" "ingest_extra" {
  statement {
    sid = "S3Put"
    actions = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.logs.arn}/*"]
  }
  statement {
    sid = "SQS"
    actions = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.analyze.arn]
  }
}

resource "aws_iam_role" "ingest_role" {
  name = "${local.ingest_name}-role"
  assume_role_policy = jsonencode({
    Version="2012-10-17", Statement=[{Effect="Allow", Principal={Service="lambda.amazonaws.com"}, Action="sts:AssumeRole"}]
  })
}

resource "aws_iam_policy" "ingest_policy" {
  name   = "${local.ingest_name}-policy"
  policy = jsonencode(merge(jsondecode(data.aws_iam_policy_document.lambda_base.json),
                            jsondecode(data.aws_iam_policy_document.ingest_extra.json)))
}

resource "aws_iam_role_policy_attachment" "ingest_attach" {
  role       = aws_iam_role.ingest_role.name
  policy_arn = aws_iam_policy.ingest_policy.arn
}

# Analyze Lambda – קריאה מ-S3, כתיבה ל-DDB, קריאת SQS
data "aws_iam_policy_document" "analyze_extra" {
  statement {
    sid = "S3RW"
    actions = ["s3:GetObject","s3:PutObject"]
    resources = ["${aws_s3_bucket.logs.arn}/*"]
  }
  statement {
    sid = "DDBPut"
    actions = ["dynamodb:PutItem"]
    resources = [aws_dynamodb_table.results.arn]
  }
  statement {
    sid = "SQSReceive"
    actions = ["sqs:ReceiveMessage","sqs:DeleteMessage","sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.analyze.arn]
  }
  statement {
    sid = "BedrockInvoke"
    actions = ["bedrock:InvokeModel"]
    resources = ["*"]
  }
}

resource "aws_iam_role" "analyze_role" {
  name = "${local.analyze_name}-role"
  assume_role_policy = jsonencode({
    Version="2012-10-17", Statement=[{Effect="Allow", Principal={Service="lambda.amazonaws.com"}, Action="sts:AssumeRole"}]
  })
}

resource "aws_iam_policy" "analyze_policy" {
  name   = "${local.analyze_name}-policy"
  policy = jsonencode(merge(jsondecode(data.aws_iam_policy_document.lambda_base.json),
                            jsondecode(data.aws_iam_policy_document.analyze_extra.json)))
}

resource "aws_iam_role_policy_attachment" "analyze_attach" {
  role       = aws_iam_role.analyze_role.name
  policy_arn = aws_iam_policy.analyze_policy.arn
}

# חבילות הלמבדה (zip) – להריץ scripts/build_packages.sh לפני apply
resource "aws_lambda_function" "ingest" {
  function_name = local.ingest_name
  role          = aws_iam_role.ingest_role.arn
  runtime       = "python3.11"
  handler       = "lambda_ingest_failure.handler"
  filename      = "${path.module}/../dist/ingest_failure.zip"
  source_code_hash = filebase64sha256("${path.module}/../dist/ingest_failure.zip")

  environment {
    variables = {
      S3_BUCKET      = aws_s3_bucket.logs.bucket
      SQS_URL        = aws_sqs_queue.analyze.id
      JENKINS_URL    = var.jenkins_url
      JENKINS_USER   = var.jenkins_user
      JENKINS_TOKEN  = var.jenkins_token
    }
  }

  timeout = 60
}

resource "aws_lambda_function" "analyze" {
  function_name = local.analyze_name
  role          = aws_iam_role.analyze_role.arn
  runtime       = "python3.11"
  handler       = "worker_analyze_failure.handler"
  filename      = "${path.module}/../dist/analyze_failure.zip"
  source_code_hash = filebase64sha256("${path.module}/../dist/analyze_failure.zip")

  environment {
    variables = {
      S3_BUCKET        = aws_s3_bucket.logs.bucket
      DDB_TABLE        = aws_dynamodb_table.results.name
      REPO_URL         = var.repo_https_url
      REPO_BRANCH      = var.repo_branch
      AZDO_PAT         = var.azdo_pat
      SLACK_WEBHOOK_URL= var.slack_webhook_url
    }
  }

  timeout = 180
}

# טריגר SQS ללמבדה analyze
resource "aws_lambda_event_source_mapping" "sqs_to_analyze" {
  event_source_arn = aws_sqs_queue.analyze.arn
  function_name    = aws_lambda_function.analyze.arn
  batch_size       = 1
}

# API Gateway HTTP → ingest
resource "aws_apigatewayv2_api" "http" {
  name          = "${var.project}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "ingest" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.ingest.arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "ingest_route" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "GET /ingest"
  target    = "integrations/${aws_apigatewayv2_integration.ingest.id}"
}

resource "aws_lambda_permission" "allow_apigw_ingest" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*/ingest"
}

output "api_endpoint"     { value = aws_apigatewayv2_api.http.api_endpoint }
output "s3_bucket"        { value = aws_s3_bucket.logs.bucket }
output "sqs_queue_url"    { value = aws_sqs_queue.analyze.id }
output "dynamodb_table"   { value = aws_dynamodb_table.results.name }
