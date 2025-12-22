# Secrets Management

QuickETL provides a pluggable secrets management system for secure credential handling in production environments.

## Overview

Instead of hardcoding credentials in your pipeline configurations, use secret references that are resolved at runtime:

```yaml
sink:
  type: database
  connection:
    host: ${secret:db/host}
    password: ${secret:db/password}
```

## Supported Providers

| Provider | Installation | Use Case |
|----------|--------------|----------|
| `env` | Built-in | Development, CI/CD |
| `aws` | `quicketl[secrets-aws]` | AWS Secrets Manager |
| `azure` | `quicketl[secrets-azure]` | Azure Key Vault |

---

## Environment Provider (Default)

The environment provider reads secrets from environment variables. No additional dependencies required.

### Configuration

```yaml
# quicketl.yml
secrets:
  provider: env
```

### Usage

```yaml
# In your pipeline
sink:
  connection:
    password: ${secret:DB_PASSWORD}  # Reads from $DB_PASSWORD env var
```

### With Defaults

```yaml
connection:
  timeout: ${secret:DB_TIMEOUT:-30}  # Default to 30 if not set
```

---

## AWS Secrets Manager

### Installation

```bash
pip install "quicketl[secrets-aws]"
```

### Configuration

```yaml
# quicketl.yml
secrets:
  provider: aws
  config:
    region: us-east-1
```

### Usage

```yaml
# Reference a secret by name
connection:
  password: ${secret:prod/database/password}

# Extract a key from a JSON secret
connection:
  host: ${secret:prod/database:host}
  password: ${secret:prod/database:password}
```

### IAM Permissions

Your execution role needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:prod/*"
    }
  ]
}
```

---

## Azure Key Vault

### Installation

```bash
pip install "quicketl[secrets-azure]"
```

### Configuration

```yaml
# quicketl.yml
secrets:
  provider: azure
  config:
    vault_url: https://my-vault.vault.azure.net/
```

### Authentication

Azure Key Vault uses `DefaultAzureCredential`, which supports:

- Managed Identity (recommended for production)
- Azure CLI credentials (for development)
- Environment variables (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`)

### Usage

```yaml
connection:
  password: ${secret:database-password}
```

---

## Environment Inheritance

Configure different secret providers per environment:

```yaml
# quicketl.yml
environments:
  base:
    secrets:
      provider: env

  dev:
    extends: base
    # Uses env provider from base

  prod:
    extends: base
    secrets:
      provider: aws
      config:
        region: us-east-1
```

Run with environment:

```bash
quicketl run pipeline.yml --env prod
```

---

## Connection Profiles

Define reusable connection profiles with secret references:

```yaml
# quicketl.yml
profiles:
  snowflake_prod:
    type: snowflake
    account: ${secret:snowflake/account}
    user: ${secret:snowflake/user}
    password: ${secret:snowflake/password}
    database: analytics
    warehouse: compute_wh

  postgres_prod:
    type: postgres
    host: ${secret:postgres/host}
    port: 5432
    database: app
    user: ${secret:postgres/user}
    password: ${secret:postgres/password}
```

Use in pipelines:

```yaml
# pipeline.yml
source:
  type: database
  profile: postgres_prod
  query: SELECT * FROM users

sink:
  type: database
  profile: snowflake_prod
  table: users
```

---

## Python API

```python
from quicketl.secrets import get_provider

# Get the configured provider
provider = get_provider("aws", region="us-east-1")

# Retrieve a secret
password = provider.get_secret("prod/database/password")

# Get a key from a JSON secret
host = provider.get_secret("prod/database", key="host")
```

---

## Best Practices

1. **Never commit secrets** - Use `.gitignore` to exclude any files with credentials
2. **Use environment-specific providers** - `env` for dev, cloud providers for prod
3. **Rotate secrets regularly** - Cloud providers support automatic rotation
4. **Least privilege** - Grant minimal IAM/RBAC permissions
5. **Audit access** - Enable logging on your secrets manager
