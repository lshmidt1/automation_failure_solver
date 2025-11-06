resource "aws_lambda_function" "ingest_failure" {
  function_name = "ingest_failure"
  handler       = "lambda_ingest_failure.handler"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_exec.arn
  source_code_hash = filebase64sha256("lambdas/ingest_failure/lambda_ingest_failure.zip")
  environment {
    # Add any environment variables here
  }
}

resource "aws_lambda_function" "analyze_failure" {
  function_name = "analyze_failure"
  handler       = "worker_analyze_failure.handler"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_exec.arn
  source_code_hash = filebase64sha256("lambdas/analyze_failure/worker_analyze_failure.zip")
  environment {
    # Add any environment variables here
  }
}

resource "aws_iam_role" "lambda_exec" {
  name = "lambda_exec_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Effect = "Allow"
        Sid    = ""
      },
    ]
  })
}

resource "aws_iam_policy_attachment" "lambda_policy" {
  name       = "lambda_policy_attachment"
  roles      = [aws_iam_role.lambda_exec.name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}