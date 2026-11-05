# snowflake-network-policy

Creates a Snowflake network policy that allows only the IP addresses you list, with the admin database, schema and network rule it needs. Use it to restrict where users can connect from.

## Usage

```hcl
provider "snowflake" {
  preview_features_enabled = ["snowflake_network_rule_resource"]
}

module "network_policy" {
  source = "git::https://github.com/ameijin/quicketl.git//terraform/modules/snowflake-network-policy?ref=v2.0.0"

  prefix = "ACME_DATA"
  # Documentation-only ranges (RFC 5737). Replace with your own.
  allowed_ips = ["203.0.113.0/24", "198.51.100.7"]
}
```

See `examples/basic/` for a complete standalone example.

The module needs the Snowflake provider `snowflakedb/snowflake ~> 2.22`. Provide credentials with `SNOWFLAKE_*` environment variables. Never put them in files.

## Inputs

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `prefix` | `string` | required | Prefix for object names, in upper case, such as `ACME_DATA`. |
| `allowed_ips` | `list(string)` | required | IPv4 addresses or CIDR (Classless Inter-Domain Routing) ranges allowed to connect, such as `["203.0.113.0/24"]`. Validation: the list must not be empty, and every entry must be an IPv4 address or CIDR range. |

## Outputs

| Name | Description |
| :--- | :--- |
| `policy_name` | Name of the network policy, to attach to the account or to users. |
| `network_rule` | Fully qualified name of the network rule. |

## Notes

- The module creates the database `<PREFIX>_ADMIN`, the schema `NETWORK` in it, the network rule `<PREFIX>_ALLOWED_IPS` (IPv4, ingress) and the network policy `<PREFIX>_NETWORK_POLICY`.
- The policy is created but not attached. Attaching it to the account blocks every other address, including other teams that use the same account. Check that the list includes your own address, then attach it yourself:

  ```sql
  ALTER ACCOUNT SET NETWORK_POLICY = <policy_name output>;
  ```

- Network rules are a preview feature in provider 2.22. The provider block of the calling configuration needs `preview_features_enabled = ["snowflake_network_rule_resource"]`, as shown in the usage snippet.
- This module has not been applied against a live Snowflake account yet. Run `terraform plan` against a sandbox account first.
