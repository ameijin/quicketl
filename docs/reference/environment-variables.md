# Environment Variables Reference

ETLX uses environment variables for configuration, database connections, and cloud credentials.

## Pipeline Variables

### Variable Substitution

Use `${VAR}` syntax in pipeline YAML:

```yaml
name: ${PIPELINE_NAME:-default}
source:
  type: file
  path: ${INPUT_PATH}/data.parquet
sink:
  type: database
  connection: ${DB_CONNECTION}
  table: ${SCHEMA}.${TABLE}
```

### Default Values

Provide defaults with `:-` syntax:

```yaml
engine: ${ENGINE:-duckdb}
source:
  type: file
  path: ${INPUT:-data/default.parquet}
```

### Setting Variables

```bash
# Command line
quicketl run pipeline.yml --var DATE=2025-01-15 --var REGION=north

# Environment
export DATE=2025-01-15
export REGION=north
quicketl run pipeline.yml

# .env file
echo "DATE=2025-01-15" >> .env
echo "REGION=north" >> .env
quicketl run pipeline.yml
```

## Database Connections

### PostgreSQL

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_PORT` | Database port | `5432` |
| `POSTGRES_USER` | Username | `etlx_user` |
| `POSTGRES_PASSWORD` | Password | `secret` |
| `POSTGRES_DATABASE` | Database name | `analytics` |
| `POSTGRES_SSLMODE` | SSL mode | `require` |
| `DATABASE_URL` | Full connection URL | `postgresql://user:pass@host:5432/db` |

```bash
# Individual variables
export POSTGRES_HOST=db.example.com
export POSTGRES_PORT=5432
export POSTGRES_USER=etlx_user
export POSTGRES_PASSWORD=secret
export POSTGRES_DATABASE=analytics

# Or connection URL
export DATABASE_URL=postgresql://etlx_user:secret@db.example.com:5432/analytics
```

### MySQL

| Variable | Description | Example |
|----------|-------------|---------|
| `MYSQL_HOST` | Database host | `localhost` |
| `MYSQL_PORT` | Database port | `3306` |
| `MYSQL_USER` | Username | `etlx_user` |
| `MYSQL_PASSWORD` | Password | `secret` |
| `MYSQL_DATABASE` | Database name | `analytics` |

### Snowflake

| Variable | Description | Example |
|----------|-------------|---------|
| `SNOWFLAKE_ACCOUNT` | Account identifier | `xy12345.us-east-1` |
| `SNOWFLAKE_USER` | Username | `etlx_user` |
| `SNOWFLAKE_PASSWORD` | Password | `secret` |
| `SNOWFLAKE_DATABASE` | Database | `analytics` |
| `SNOWFLAKE_SCHEMA` | Schema | `public` |
| `SNOWFLAKE_WAREHOUSE` | Warehouse | `compute_wh` |
| `SNOWFLAKE_ROLE` | Role | `analyst` |
| `SNOWFLAKE_PRIVATE_KEY_PATH` | Key file path | `/path/to/key.p8` |

```bash
export SNOWFLAKE_ACCOUNT=xy12345.us-east-1
export SNOWFLAKE_USER=etlx_user
export SNOWFLAKE_PASSWORD=secret
export SNOWFLAKE_DATABASE=analytics
export SNOWFLAKE_SCHEMA=public
export SNOWFLAKE_WAREHOUSE=etl_wh
```

### BigQuery

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account JSON | `/path/to/sa.json` |
| `BIGQUERY_PROJECT` | GCP project ID | `my-project-123` |
| `BIGQUERY_DATASET` | Default dataset | `analytics` |
| `BIGQUERY_LOCATION` | Location | `US` |

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export BIGQUERY_PROJECT=my-project-123
export BIGQUERY_DATASET=analytics
```

### ClickHouse

| Variable | Description | Example |
|----------|-------------|---------|
| `CLICKHOUSE_HOST` | Server host | `localhost` |
| `CLICKHOUSE_PORT` | HTTP port | `8123` |
| `CLICKHOUSE_USER` | Username | `default` |
| `CLICKHOUSE_PASSWORD` | Password | `secret` |
| `CLICKHOUSE_DATABASE` | Database | `analytics` |

## Cloud Storage

### AWS S3

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | Access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | Secret key | `wJal...` |
| `AWS_SESSION_TOKEN` | Session token (STS) | `FwoG...` |
| `AWS_REGION` | Default region | `us-east-1` |
| `AWS_DEFAULT_REGION` | Alternative region var | `us-east-1` |

```bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_REGION=us-east-1
```

Or use AWS CLI profiles:

```bash
export AWS_PROFILE=production
```

### Google Cloud Storage

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account | `/path/to/sa.json` |
| `GOOGLE_CLOUD_PROJECT` | Project ID | `my-project-123` |

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

Or use gcloud CLI:

```bash
gcloud auth application-default login
```

### Azure Blob Storage

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_STORAGE_ACCOUNT` | Storage account | `mystorageaccount` |
| `AZURE_STORAGE_KEY` | Access key | `abc123...` |
| `AZURE_STORAGE_CONNECTION_STRING` | Connection string | `DefaultEndpoints...` |

```bash
export AZURE_STORAGE_ACCOUNT=mystorageaccount
export AZURE_STORAGE_KEY=abc123...
```

## Spark Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `SPARK_MASTER` | Spark master URL | `local[*]`, `spark://host:7077` |
| `SPARK_EXECUTOR_MEMORY` | Executor memory | `4g` |
| `SPARK_EXECUTOR_CORES` | Executor cores | `2` |
| `SPARK_EXECUTOR_INSTANCES` | Number of executors | `10` |
| `SPARK_DRIVER_MEMORY` | Driver memory | `2g` |

```bash
export SPARK_MASTER=local[*]
export SPARK_EXECUTOR_MEMORY=8g
export SPARK_EXECUTOR_CORES=4
```

## ETLX Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ETLX_LOG_LEVEL` | Logging level | `INFO` |
| `ETLX_CONFIG_DIR` | Config directory | `.` |
| `ETLX_CACHE_DIR` | Cache directory | `~/.cache/etlx` |

```bash
export ETLX_LOG_LEVEL=DEBUG
```

## Using .env Files

Create a `.env` file in your project root:

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/db
AWS_REGION=us-east-1
SNOWFLAKE_ACCOUNT=xy12345.us-east-1
SNOWFLAKE_USER=etlx_user
SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD}  # Reference secrets manager
```

ETLX automatically loads `.env` files.

## Environment-Specific Configuration

### Development

```bash
# .env.development
DATABASE_URL=postgresql://dev:dev@localhost:5432/dev_db
S3_BUCKET=dev-data-lake
LOG_LEVEL=DEBUG
```

### Production

```bash
# .env.production
DATABASE_URL=postgresql://prod:${DB_PASSWORD}@prod-db:5432/prod_db
S3_BUCKET=prod-data-lake
LOG_LEVEL=INFO
```

### Loading Environment Files

```bash
# Load specific env file
export $(cat .env.production | xargs)
quicketl run pipeline.yml
```

## Secrets Management

### Never Commit Secrets

```bash
# .gitignore
.env
.env.*
*.pem
*.key
credentials.json
```

### Use Secret References

```bash
# .env
DATABASE_PASSWORD=${DB_PASSWORD_FROM_VAULT}
SNOWFLAKE_PASSWORD=$(vault kv get -field=password secret/snowflake)
```

### Secret Managers

```bash
# AWS Secrets Manager
export DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id prod/db-password \
  --query SecretString --output text)

# HashiCorp Vault
export DB_PASSWORD=$(vault kv get -field=password secret/database)

# Google Secret Manager
export DB_PASSWORD=$(gcloud secrets versions access latest --secret=db-password)
```

## Debugging

### View Current Environment

```bash
# Show all ETLX-related variables
env | grep -E '^(ETLX_|POSTGRES_|SNOWFLAKE_|AWS_|GOOGLE_)'

# Test variable substitution
quicketl validate pipeline.yml --verbose
```

### Common Issues

**Variable not expanding:**

```bash
# Wrong: Single quotes prevent expansion
export PATH='${HOME}/data'  # Literal ${HOME}

# Right: Double quotes or no quotes
export PATH="${HOME}/data"  # Expands to /home/user/data
```

**Missing variable:**

```yaml
# Use defaults to handle missing variables
path: ${INPUT_PATH:-data/default.parquet}
```

## Related

- [Pipeline YAML](../user-guide/configuration/pipeline-yaml.md) - YAML syntax
- [Variables](../user-guide/configuration/variables.md) - Variable substitution
- [Production Best Practices](../best-practices/production.md) - Secrets management
