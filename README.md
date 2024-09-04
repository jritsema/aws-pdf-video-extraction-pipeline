# aws-pdf-video-extraction-pipeline

Extract text and transcriptions from PDFs and videos uploaded to an S3 bucket.

This project deploys an S3 Lambda trigger. It performs the following tasks:

1. **PDF Processing**:
   - When a PDF file is uploaded, the function extracts images from the PDF.
   - It then processes the extracted images using Amazon Textract, an AWS service for optical character recognition (OCR).
   - The extracted text from the images is then uploaded to the same S3 bucket, with the file path modified to include the image name and "textract.txt".

2. **Video Processing**:
   - When a video file (e.g., `.mp4`) is uploaded, the function submits a transcription job to Amazon Transcribe, an AWS service for speech-to-text conversion.
   - The transcription output is then uploaded to the S3 bucket, with the file path modified to include the original file name and "transcribe.out".

3. **Transcription Processing**:
   - When the transcription output file (with the ".transcribe.out" extension) is uploaded, the function reads the JSON data, extracts the transcript, and uploads it to the S3 bucket with the file path modified to include the original file name and "transcribe.txt".
   - After the transcript is uploaded, the function deletes the intermediate artifacts (the ".transcribe.out" file and any associated objects) from the S3 bucket.


### Usage

Optional - register pre-commit hooks and asdf for deps.

```sh
make init
```

Deploy the infra. S3 trigger to Lambda container.

```sh
terraform init && terraform apply
```

Deploy code changes (uses containers on Lambda).

[Setup python environment for local dev.](./lambda/README.md)

```sh
cd lambda
make init
```

```sh
make deploy-container function=my-function
```

### Terraform

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 5.0 |
| <a name="requirement_docker"></a> [docker](#requirement\_docker) | >= 3.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | ~> 5.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_docker_image"></a> [docker\_image](#module\_docker\_image) | terraform-aws-modules/lambda/aws//modules/docker-build | n/a |
| <a name="module_lambda"></a> [lambda](#module\_lambda) | terraform-aws-modules/lambda/aws | n/a |

## Resources

| Name | Type |
|------|------|
| [aws_iam_role.lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy_attachment.test_attach](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_s3_bucket_notification.main](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_notification) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_ecr_authorization_token.token](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ecr_authorization_token) | data source |
| [aws_s3_bucket.main](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/s3_bucket) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_region"></a> [region](#input\_region) | region | `string` | `"us-east-1"` | no |
| <a name="input_s3_bucket"></a> [s3\_bucket](#input\_s3\_bucket) | s3 bucket to run image extraction against | `string` | n/a | yes |

## Outputs

No outputs.
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
