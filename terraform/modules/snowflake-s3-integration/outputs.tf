output "name" {
  description = "Name of the storage integration."
  value       = snowflake_storage_integration_aws.this.name
}

output "iam_user_arn" {
  description = "AWS IAM user Snowflake uses; add it to the IAM role's trust policy."
  value       = snowflake_storage_integration_aws.this.describe_output[0].iam_user_arn
}

output "external_id" {
  description = "External ID to require in the IAM role's trust policy."
  value       = snowflake_storage_integration_aws.this.describe_output[0].external_id
}
