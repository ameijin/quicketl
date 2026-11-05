# Standalone use of the snowflake-network-policy module. Network rules are a
# preview feature in provider 2.22, so the provider turns them on.

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
  preview_features_enabled = ["snowflake_network_rule_resource"]
}

module "network_policy" {
  source = "../.."

  prefix = "ACME_DATA"
  # Documentation-only ranges (RFC 5737). Replace with your own.
  allowed_ips = ["203.0.113.0/24", "198.51.100.7"]
}

output "policy_name" {
  value = module.network_policy.policy_name
}
