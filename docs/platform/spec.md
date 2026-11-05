# Platform Spec (platform.yml)

A platform spec is one small YAML file that describes the data platform you want: the warehouse, environments, data layers, business domains, who can access what, where raw files land, and how loads are scheduled. Write one when you start a new platform. Platform templates will read it to generate Terraform, dbt and Airflow code.

!!! note "What works today"
    You can create a starter spec with `quicketl platform init`, check it with `quicketl platform validate`, and generate a project from it with `quicketl platform scaffold` (see [Scaffold and Update](scaffold.md)). The Snowflake template generates Terraform so far; dbt and Airflow come later. See [ADR 0010](../adr/0010-platform-spec.md).

Checking a spec needs only the core install (`pip install quicketl`). It does not connect to AWS or your warehouse.

## Start from a template

```bash
quicketl platform init my-platform
```

This writes `my-platform/platform.yml` with a comment on every section. Edit it, then run `quicketl platform validate`. See the [CLI reference](../reference/cli.md#platform) for options.

## Example

```yaml
name: acme_data

warehouse:
  type: snowflake

environments: [dev, prod]
layers: [raw, staging, marts]

domains:
  - name: sales
    description: Orders, customers and returns

roles:
  - name: transformer
    description: Service user that runs dbt
    access: {raw: read, staging: write, marts: write}
  - name: analyst
    access: {marts: read}
    domains: [sales]

sso:
  provider: okta

network:
  allowed_ips: [203.0.113.0/24]

sources:
  - name: orders
    domain: sales
    location: s3://example-landing/sales/orders/
    format: parquet

orchestrator:
  type: airflow
  hosting: mwaa
  schedule: "@daily"
```

Check it:

```bash
quicketl platform validate platform.yml
```

A complete, runnable version is in [`examples/06-platform-spec`](https://github.com/ameijin/quicketl/tree/main/examples/06-platform-spec).

## Only three fields are required

```yaml
name: acme_data
warehouse:
  type: snowflake
domains:
  - name: sales
```

Everything else has a default, listed below.

## Fields

### Top level

| Field | Required | Default | What it means |
|-------|----------|---------|---------------|
| `version` | No | `"1"` | Spec format version. Only `"1"` exists. |
| `name` | Yes | | Platform name. Templates use it as a prefix for warehouse objects. |
| `warehouse` | Yes | | The warehouse the platform runs on. |
| `environments` | No | `[dev, prod]` | Environment names. Each one gets its own databases and grants. At least one. |
| `layers` | No | `[raw, staging, marts]` | Data layers, in order. Sources load into the first one. At least one. |
| `domains` | Yes | | Business areas that own their own data. At least one. |
| `roles` | No | `[]` | Functional roles and what they can access. |
| `sso` | No | `provider: none` | Single sign-on (SSO) for warehouse users. |
| `network` | No | no rules | IP ranges allowed to connect. |
| `sources` | No | `[]` | Raw files that land in S3. |
| `orchestrator` | No | Airflow on MWAA, `@daily` | How loads and dbt runs are scheduled. |

### warehouse

| Field | Values |
|-------|--------|
| `type` | `snowflake`, `databricks` or `redshift_serverless` |

The first template is for Snowflake. Databricks and Redshift Serverless templates come later, so a spec for them validates but cannot be scaffolded yet.

### domains

| Field | Required | What it means |
|-------|----------|---------------|
| `name` | Yes | Domain name, such as `sales`. |
| `description` | No | One line saying what data the domain holds. |

### roles

A role is a kind of user, such as an analyst or the service user that runs dbt. Templates turn each role into warehouse roles and grants.

| Field | Required | What it means |
|-------|----------|---------------|
| `name` | Yes | Role name, such as `analyst`. |
| `description` | No | One line saying who gets this role. |
| `access` | Yes | Map of layer name to `read` or `write`. `read` can query the layer. `write` can also create and change objects in it. At least one entry. |
| `domains` | No | Domains the role covers. Leave it out to cover every domain. |

### sso

| Field | Values |
|-------|--------|
| `provider` | `okta` or `none` (default). |

### network

| Field | What it means |
|-------|---------------|
| `allowed_ips` | List of IP addresses (`198.51.100.7`) or CIDR ranges (`203.0.113.0/24`). Empty means templates add no network policy. |

A range must start on its boundary: write `10.0.0.0/24`, not `10.0.0.1/24`. The second form is almost always a typo, so it is rejected.

### sources

| Field | Required | Default | What it means |
|-------|----------|---------|---------------|
| `name` | Yes | | Source name, such as `orders`. |
| `domain` | Yes | | The domain that owns this source. |
| `location` | Yes | | S3 prefix the files land in. Must start with `s3://`. |
| `format` | No | `parquet` | `csv`, `parquet` or `json`. |

Generated projects load sources with the warehouse's own loader, such as Snowflake `COPY INTO`. See [ADR 0006](../adr/0006-native-loaders-and-dbt-tests.md).

### orchestrator

| Field | Default | Values |
|-------|---------|--------|
| `type` | `airflow` | `airflow` |
| `hosting` | `mwaa` | `mwaa` (Amazon Managed Workflows for Apache Airflow) |
| `schedule` | `@daily` | An Airflow preset such as `@hourly`, or a cron expression. Not checked by `validate`. |

## Rules `validate` checks

- **Names** (platform, environments, layers, domains, roles, sources) start with a lowercase letter and use only lowercase letters, digits and underscores, because they become warehouse object names.
- **No duplicates** within environments, layers, domains, roles or sources.
- **References exist:** every layer in a role's `access`, every domain in a role's `domains`, and every source's `domain` must be defined in the spec.
- **No unknown keys.** A typo such as `enviroments:` is an error, not silently ignored.

Problems inside one field are reported with their location, for example `roles -> 1 -> access -> marts`. Reference problems are checked once every field is valid, and all of them are reported together.

## What does not go in the spec

The spec stays small on purpose. Warehouse sizes, Terraform provider settings, account identifiers and DAG details live in the generated project, where your team edits them directly. Never put passwords, keys or tokens in `platform.yml`.

## Use it from Python

```python
from quicketl.platform import load_platform_spec

spec = load_platform_spec("platform.yml")
print(spec.warehouse.type, spec.landing_layer)
```

`load_platform_spec` raises `PlatformSpecError` if the file is missing, empty or not YAML, and `pydantic.ValidationError` if the contents break the rules above.
