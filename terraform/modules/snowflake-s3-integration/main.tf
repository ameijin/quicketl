# Storage integration that lets Snowflake read S3 locations. After apply, add
# the outputs iam_user_arn and external_id to the trust policy of
# var.storage_aws_role_arn in AWS.

resource "snowflake_storage_integration_aws" "this" {
  name                      = var.name
  enabled                   = true
  storage_provider          = "S3"
  storage_aws_role_arn      = var.storage_aws_role_arn
  storage_allowed_locations = var.allowed_locations
}

# Roles that create stages on this integration need USAGE on it.
resource "snowflake_grant_privileges_to_account_role" "usage" {
  for_each = toset(var.usage_roles)

  account_role_name = each.value
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "INTEGRATION"
    object_name = snowflake_storage_integration_aws.this.name
  }
}
