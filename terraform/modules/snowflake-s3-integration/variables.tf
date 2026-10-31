variable "name" {
  description = "Name of the storage integration, such as ACME_DATA_S3_LANDING."
  type        = string
}

variable "storage_aws_role_arn" {
  description = "ARN of the AWS IAM role Snowflake assumes to read the bucket."
  type        = string
}

variable "allowed_locations" {
  description = "S3 prefixes the integration may read, such as [\"s3://bucket/sales/\"]."
  type        = list(string)

  validation {
    condition     = length(var.allowed_locations) > 0 && alltrue([for loc in var.allowed_locations : startswith(loc, "s3://")])
    error_message = "allowed_locations must be a non-empty list of s3:// prefixes."
  }
}

variable "usage_roles" {
  description = "Account role names to grant USAGE on the integration, such as the loader role."
  type        = list(string)
  default     = []
}
