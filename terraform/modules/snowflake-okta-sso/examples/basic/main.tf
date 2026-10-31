# Standalone use of the snowflake-okta-sso module. Pass the Okta values with
# TF_VAR_okta_* environment variables or a .tfvars file kept out of git.

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

variable "okta_saml_issuer" {
  type = string
}

variable "okta_sso_url" {
  type = string
}

variable "okta_x509_cert" {
  type      = string
  sensitive = true
}

module "okta_sso" {
  source = "../.."

  prefix      = "ACME_DATA"
  saml_issuer = var.okta_saml_issuer
  sso_url     = var.okta_sso_url
  x509_cert   = var.okta_x509_cert
}

output "scim_integration" {
  value = module.okta_sso.scim_integration
}
