# Standalone use of the snowflake-s3-integration module. The AWS storage
# integration is a preview feature in provider 2.22, so the provider turns it on.

terraform {
  required_version = ">= 1.5"

  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.22"
    }
  }
}

provider "snowflake" {
  preview_features_enabled = ["snowflake_storage_integration_aws_resource"]
}

variable "storage_aws_role_arn" {
  description = "ARN of the IAM role Snowflake assumes."
  type        = string
}

module "s3_integration" {
  source = "../.."

  name                 = "ACME_DATA_S3_LANDING"
  storage_aws_role_arn = var.storage_aws_role_arn
  allowed_locations    = ["s3://example-landing/sales/", "s3://example-landing/finance/"]
  usage_roles          = ["ACME_DATA_DEV_LOADER"]
}

output "trust_policy_values" {
  value = {
    iam_user_arn = module.s3_integration.iam_user_arn
    external_id  = module.s3_integration.external_id
  }
}
