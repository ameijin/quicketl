# snowflake-platform

Creates the core Snowflake layout for a data platform: databases, schemas, warehouses, access roles and functional roles. Use it to set up a new platform with one consistent naming and permission model.

## Usage

```hcl
module "platform" {
  source = "git::https://github.com/ameijin/quicketl.git//terraform/modules/snowflake-platform?ref=v2.0.0"

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
```

See `examples/basic/` for a complete standalone example.

The module needs the Snowflake provider `snowflakedb/snowflake ~> 2.22`. Provide credentials with `SNOWFLAKE_*` environment variables. Never put them in files.

## Inputs

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `prefix` | `string` | required | Prefix for every object name, in upper case, such as `ACME_DATA`. Validation: upper case letters, digits and underscores only, starting with a letter. |
| `environments` | `list(string)` | required | Environment names in upper case, such as `["DEV", "PROD"]`. Each gets its own databases and warehouse. |
| `layers` | `list(string)` | required | Data layers in order, in upper case, such as `["RAW", "STAGING", "MARTS"]`. The first is the landing layer. |
| `domains` | `list(string)` | required | Business domains in upper case, such as `["SALES"]`. Each becomes a schema in every database. |
| `roles` | `map(object({ access = map(string), domains = list(string) }))` | `{}` | Functional roles by name (upper case). `access` maps a layer to `"read"` or `"write"`. `domains` lists the domains the role covers. Validation: every access level must be `"read"` or `"write"`. |
| `warehouse_sizes` | `map(string)` | `{}` | Warehouse size per environment, such as `{ PROD = "SMALL" }`. Environments not listed use `XSMALL`. |

## Outputs

| Name | Description |
| :--- | :--- |
| `databases` | Database names by `<ENV>_<LAYER>`. |
| `schemas` | Fully qualified schema names by `<ENV>_<LAYER>_<DOMAIN>`. |
| `warehouses` | Warehouse names by environment. |
| `access_roles` | Access role names by `<ENV>_<LAYER>_<DOMAIN>_R` or `..._W`. |
| `functional_roles` | Functional role names by `<ENV>_<ROLE>`. |
| `landing_writer_roles` | Functional role names that can write the landing layer (the first layer). |

## Notes

Naming:

- Databases: `<PREFIX>_<ENV>_<LAYER>`, one per environment and layer.
- Schemas: one per domain in every database, created with managed access.
- Warehouses: `<PREFIX>_<ENV>_WH`, one per environment. The size is `XSMALL` unless `warehouse_sizes` says otherwise. Each warehouse suspends after 60 seconds, resumes automatically and starts suspended.
- Access roles: `<PREFIX>_<ENV>_<LAYER>_<DOMAIN>_R` and `..._W`, one pair per schema. The `_W` role also holds the `_R` role, so write includes read.
- Functional roles: `<PREFIX>_<ENV>_<ROLE>`, one per environment and role. Each rolls up to `SYSADMIN`.

Privileges (from `grants.tf`):

- Read (`_R`): `USAGE` on the database and the schema, and `SELECT` on all current and future tables and views in the schema.
- Write (`_W`): `CREATE TABLE`, `CREATE VIEW`, `CREATE STAGE` and `CREATE FILE FORMAT` on the schema, and `INSERT`, `UPDATE`, `DELETE` and `TRUNCATE` on all current and future tables in the schema. It also has everything in read, through the `_R` role.
- Functional roles: `USAGE` on the warehouse of their environment, plus the access roles for each layer and domain listed in their `access` and `domains`.

Give people functional roles only. Do not grant access roles to people directly.

This module has not been applied against a live Snowflake account yet. Run `terraform plan` against a sandbox account first.
