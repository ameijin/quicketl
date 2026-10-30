# Example: Platform spec

A `platform.yml` for a small Snowflake platform with two domains, three roles, Okta sign-in and two S3 sources. It shows every section of the spec.

This example needs only the core install (`pip install quicketl`).

## Run

```bash
cd examples/06-platform-spec
quicketl platform validate
```

You should see `Platform spec is valid` and a summary:

```text
  Warehouse: snowflake
  Environments: dev, prod
  Layers: raw, staging, marts
  Domains: 2
  Roles: 3
  Sources: 2
  SSO: okta
  Orchestrator: airflow on mwaa
```

## Try a mistake

Change the analyst role's access to `{gold: read}` and run the command again. It fails with:

```text
role 'analyst' refers to unknown layer 'gold'
```

The S3 bucket and IP ranges are placeholders. Validation does not connect to AWS or Snowflake.

See the [platform spec guide](../../docs/platform/spec.md) for every field.
