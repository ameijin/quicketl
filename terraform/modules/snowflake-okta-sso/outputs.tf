output "saml_integration" {
  description = "Name of the SAML integration."
  value       = snowflake_saml2_integration.okta.name
}

output "scim_integration" {
  description = "Name of the SCIM integration. Generate Okta's token with SYSTEM$GENERATE_SCIM_ACCESS_TOKEN('<this name>')."
  value       = snowflake_scim_integration.okta.name
}
