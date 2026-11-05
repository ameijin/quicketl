# Standalone use of the snowflake-platform module, without a quicketl
# template. Credentials come from SNOWFLAKE_* environment variables.

terraform {
  required_version = ">= 1.5"

  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.22"
    }
  }
}

provider "snowflake" {}

module "platform" {
  source = "../.."

  prefix       = "ACME_DATA"
  environments = ["DEV", "PROD"]
  layers       = ["RAW", "STAGING", "MARTS"]
  domains      = ["SALES", "FINANCE"]
  roles = {
    LOADER      = { access = { RAW = "write" }, domains = ["SALES", "FINANCE"] }
    TRANSFORMER = { access = { RAW = "read", STAGING = "write", MARTS = "write" }, domains = ["SALES", "FINANCE"] }
    ANALYST     = { access = { MARTS = "read" }, domains = ["SALES"] }
  }
  warehouse_sizes = { PROD = "SMALL" }
}

output "functional_roles" {
  value = module.platform.functional_roles
}
