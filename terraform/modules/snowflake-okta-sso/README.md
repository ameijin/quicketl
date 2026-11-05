# snowflake-okta-sso

Sets up Okta single sign-on (SAML, Security Assertion Markup Language) and user provisioning (SCIM, System for Cross-domain Identity Management) in Snowflake. Use it when Okta manages your users.

## Usage

```hcl
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
  source = "git::https://github.com/ameijin/quicketl.git//terraform/modules/snowflake-okta-sso?ref=v2.0.0"

  prefix      = "ACME_DATA"
  saml_issuer = var.okta_saml_issuer
  sso_url     = var.okta_sso_url
  x509_cert   = var.okta_x509_cert
}
```

See `examples/basic/` for a complete standalone example.

The module needs the Snowflake provider `snowflakedb/snowflake ~> 2.22`. Provide credentials with `SNOWFLAKE_*` environment variables. Never put them in files.

## Inputs

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `prefix` | `string` | required | Prefix for integration names, in upper case, such as `ACME_DATA`. |
| `saml_issuer` | `string` | required | Okta identity provider issuer, from the Okta Snowflake app's SAML settings. |
| `sso_url` | `string` | required | Okta single sign-on URL, from the Okta Snowflake app's SAML settings. |
| `x509_cert` | `string` | required | Okta signing certificate: the base64 body only, without BEGIN and END lines. Marked sensitive. |

## Outputs

| Name | Description |
| :--- | :--- |
| `saml_integration` | Name of the SAML integration. |
| `scim_integration` | Name of the SCIM integration. Generate Okta's token with `SYSTEM$GENERATE_SCIM_ACCESS_TOKEN('<this name>')`. |

## Notes

- The module creates the SAML integration `<PREFIX>_OKTA_SAML`, the SCIM integration `<PREFIX>_OKTA_SCIM`, and the role `OKTA_PROVISIONER`. The role gets `CREATE USER` and `CREATE ROLE` on the account and is granted to `ACCOUNTADMIN`. The SCIM integration runs as this role.
- `OKTA_PROVISIONER` is an account-wide role name. Use this module once per account.
- Generate the Okta SCIM token in Snowflake with the `scim_integration` output:

  ```sql
  SELECT SYSTEM$GENERATE_SCIM_ACCESS_TOKEN('<scim_integration output>');
  ```

- Keep the certificate out of git. Pass it with a `TF_VAR_okta_x509_cert` environment variable, or with a `.tfvars` file that is git-ignored.
- This module has not been applied against a live Snowflake account yet. Run `terraform plan` against a sandbox account first.
