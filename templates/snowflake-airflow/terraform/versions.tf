terraform {
  required_version = ">= 1.11" # for S3 state lock files (use_lockfile)

  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.22"
    }
  }
}
