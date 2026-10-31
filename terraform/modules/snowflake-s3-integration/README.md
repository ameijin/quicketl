# snowflake-s3-integration

Creates a Snowflake storage integration that lets Snowflake read from Amazon S3 locations, and grants `USAGE` on it to the roles you name. Use it before you create external stages on S3 data.

## Usage

```hcl
provider "snowflake" {
  preview_features_enabled = ["snowflake_storage_integration_aws_resource"]
}

module "s3_integration" {
  source = "git::https://github.com/ameijin/quicketl.git//terraform/modules/snowflake-s3-integration?ref=v2.0.0"

  name                 = "ACME_DATA_S3_LANDING"
  storage_aws_role_arn = var.storage_aws_role_arn
  allowed_locations    = ["s3://example-landing/sales/", "s3://example-landing/finance/"]
  usage_roles          = ["ACME_DATA_DEV_LOADER"]
}
```

See `examples/basic/` for a complete standalone example.

The module needs the Snowflake provider `snowflakedb/snowflake ~> 2.22`. Provide credentials with `SNOWFLAKE_*` environment variables. Never put them in files.

## Inputs

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `name` | `string` | required | Name of the storage integration, such as `ACME_DATA_S3_LANDING`. |
| `storage_aws_role_arn` | `string` | required | ARN (Amazon Resource Name) of the AWS IAM (Identity and Access Management) role Snowflake assumes to read the bucket. |
| `allowed_locations` | `list(string)` | required | S3 prefixes the integration may read, such as `["s3://bucket/sales/"]`. Validation: the list must not be empty, and every entry must start with `s3://`. |
| `usage_roles` | `list(string)` | `[]` | Account role names to grant `USAGE` on the integration, such as the loader role. |

## Outputs

| Name | Description |
| :--- | :--- |
| `name` | Name of the storage integration. |
| `iam_user_arn` | AWS IAM user Snowflake uses; add it to the IAM role's trust policy. |
| `external_id` | External ID to require in the IAM role's trust policy. |

## Notes

- After `terraform apply`, add the outputs `iam_user_arn` and `external_id` to the trust policy of the IAM role in `storage_aws_role_arn`.
- The roles in `usage_roles` get `USAGE` on the integration so they can create stages that use it.
- The AWS storage integration is a preview feature in provider 2.22. The provider block of the calling configuration needs `preview_features_enabled = ["snowflake_storage_integration_aws_resource"]`, as shown in the usage snippet.
- This module has not been applied against a live Snowflake account yet. Run `terraform plan` against a sandbox account first.
