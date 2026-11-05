# Terraform Modules

quicketl's Terraform lives in four modules in the repo's `terraform/modules/` folder. Platform templates call them, and you can use any of them on its own, for example to add a network policy to a Snowflake account you already manage.

| Module | What it creates |
|--------|-----------------|
| [`snowflake-platform`](https://github.com/ameijin/quicketl/tree/main/terraform/modules/snowflake-platform) | Databases per environment and layer, a schema per domain, a warehouse per environment, read and write access roles per schema, and functional roles with their grants. |
| [`snowflake-network-policy`](https://github.com/ameijin/quicketl/tree/main/terraform/modules/snowflake-network-policy) | A network rule and network policy for a list of IP ranges. Created, not attached. |
| [`snowflake-s3-integration`](https://github.com/ameijin/quicketl/tree/main/terraform/modules/snowflake-s3-integration) | An S3 storage integration, with `USAGE` for the roles you name. |
| [`snowflake-okta-sso`](https://github.com/ameijin/quicketl/tree/main/terraform/modules/snowflake-okta-sso) | Okta sign-in (SAML) and user provisioning (SCIM). |

Each module's README lists its inputs and outputs, and `examples/basic/` shows it used alone.

## Use one module in your own Terraform

Pin the module to a quicketl release tag:

```hcl
module "network_policy" {
  source = "git::https://github.com/ameijin/quicketl.git//terraform/modules/snowflake-network-policy?ref=v2.0.0"

  prefix      = "ACME_DATA"
  allowed_ips = ["203.0.113.0/24"]
}
```

Then:

1. Use the Snowflake provider `snowflakedb/snowflake ~> 2.22`, with credentials from `SNOWFLAKE_*` environment variables.
2. Turn on any preview features the module's README lists, in your own `provider "snowflake"` block. Modules never configure the provider.
3. Run `terraform init`, then `terraform plan`, and read the plan before you apply it.

To move to a newer release, change `ref` and run `terraform init -upgrade`.

## How generated projects use them

A project made by `quicketl platform scaffold` calls the modules from git, pinned to the tag it was scaffolded from. `quicketl platform update --ref <tag>` moves the template and the modules to that tag together. To change a module's code for one project, copy the module into the project and point `source` at the copy; that project then stops getting module fixes.

## How the modules are checked

`scripts/check_templates.py` runs `terraform fmt -check`, `terraform init` and `terraform validate` on each module's example, and checks every attribute reference against the provider schema. CI runs it in the `templates` job. None of the modules has been applied against a live Snowflake account yet.

The design is recorded in [ADR 0015](../adr/0015-terraform-modules.md).
