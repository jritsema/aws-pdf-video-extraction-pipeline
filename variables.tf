variable "region" {
  description = "region"
  type        = string
  default     = "us-east-1"
}

variable "s3_bucket" {
  description = "s3 bucket to run image extraction against"
  type        = string
}
