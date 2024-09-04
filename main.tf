provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}

provider "docker" {
  registry_auth {
    address  = format("%v.dkr.ecr.%v.amazonaws.com", local.account, var.region)
    username = data.aws_ecr_authorization_token.token.user_name
    password = data.aws_ecr_authorization_token.token.password
  }
}

locals {
  account = data.aws_caller_identity.current.account_id
  tags = {
    name        = local.name
    application = local.name
  }

  name = "${var.s3_bucket}-create-notification"
}

data "aws_s3_bucket" "main" {
  bucket = var.s3_bucket
}

module "docker_image" {
  source = "terraform-aws-modules/lambda/aws//modules/docker-build"

  create_ecr_repo = true
  ecr_repo        = local.name
  image_tag       = "latest"
  source_path     = "${path.module}/lambda/"
  platform        = "linux/amd64"
}

module "lambda" {
  source = "terraform-aws-modules/lambda/aws"

  function_name  = local.name
  description    = "trigged when new objects are created in the ${var.s3_bucket} bucket"
  create_package = false
  package_type   = "Image"
  image_uri      = module.docker_image.image_uri
  memory_size    = 1024
  timeout        = 300

  create_current_version_allowed_triggers = false
  allowed_triggers = {
    Rule = {
      principal  = "s3.amazonaws.com"
      source_arn = data.aws_s3_bucket.main.arn
    }
  }

  create_role = false
  lambda_role = aws_iam_role.lambda.arn
}

resource "aws_s3_bucket_notification" "main" {
  bucket = var.s3_bucket

  lambda_function {
    lambda_function_arn = module.lambda.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
  }
}

resource "aws_iam_role" "lambda" {
  name               = local.name
  assume_role_policy = <<JSON
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "lambda",
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    },
    {
      "Sid": "transcribe",
      "Effect": "Allow",
      "Principal": {
        "Service": "transcribe.amazonaws.com"
      },
      "Action": [
        "sts:AssumeRole"
      ],
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "${local.account}"
        },
        "StringLike": {
          "aws:SourceArn": "arn:aws:transcribe:${var.region}:${local.account}:*"
        }
      }
    }
  ]
}
  JSON

  inline_policy {
    name = "lambda_permissions"

    policy = <<EOT
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "s3",
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": [
        "${data.aws_s3_bucket.main.arn}",
        "${data.aws_s3_bucket.main.arn}/*"
      ]
    },
    {
      "Sid": "textract",
      "Effect": "Allow",
      "Action": "textract:AnalyzeDocument",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "transcribe:StartTranscriptionJob",
      "Resource": "*"
    }
  ]
}
EOT
  }
}

resource "aws_iam_role_policy_attachment" "test_attach" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
