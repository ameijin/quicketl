variable "prefix" {
  description = "Prefix for integration names, in upper case, such as ACME_DATA."
  type        = string
}

variable "saml_issuer" {
  description = "Okta identity provider issuer, from the Okta Snowflake app's SAML settings."
  type        = string
}

variable "sso_url" {
  description = "Okta single sign-on URL, from the Okta Snowflake app's SAML settings."
  type        = string
}

variable "x509_cert" {
  description = "Okta signing certificate: the base64 body only, without BEGIN and END lines."
  type        = string
  sensitive   = true
}
