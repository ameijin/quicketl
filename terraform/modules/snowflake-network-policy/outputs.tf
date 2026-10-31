output "policy_name" {
  description = "Name of the network policy, to attach to the account or to users."
  value       = snowflake_network_policy.this.name
}

output "network_rule" {
  description = "Fully qualified name of the network rule."
  value       = snowflake_network_rule.allowed_ips.fully_qualified_name
}
