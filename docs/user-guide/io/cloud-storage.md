# Cloud Storage

Read and write files from AWS S3, Google Cloud Storage, and Azure ADLS.

## Overview

QuickETL supports cloud storage through [fsspec](https://filesystem-spec.readthedocs.io/), providing a unified interface for all cloud providers.

## AWS S3

### Installation

```bash
pip install quicketl[aws]
```

### Configuration

```yaml
source:
  type: file
  path: s3://my-bucket/data/sales.parquet
  format: parquet
```

### Authentication

#### Environment Variables (Recommended)

```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
```

#### AWS Profile

```bash
export AWS_PROFILE=my-profile
```

#### IAM Role

When running on AWS (EC2, ECS, Lambda), IAM roles are automatically used.

### Examples

Read from S3:

```yaml
source:
  type: file
  path: s3://data-lake/raw/sales/2025/01/15/data.parquet
```

Write to S3:

```yaml
sink:
  type: file
  path: s3://data-lake/processed/sales/
  format: parquet
```

With variables:

```yaml
source:
  type: file
  path: s3://${BUCKET}/data/${DATE}/sales.parquet
```

## Google Cloud Storage

### Installation

```bash
pip install quicketl[gcp]
```

### Configuration

```yaml
source:
  type: file
  path: gs://my-bucket/data/sales.parquet
  format: parquet
```

### Authentication

#### Service Account Key

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

#### Application Default Credentials

```bash
gcloud auth application-default login
```

### Examples

Read from GCS:

```yaml
source:
  type: file
  path: gs://data-lake/raw/sales.parquet
```

Write to GCS:

```yaml
sink:
  type: file
  path: gs://data-lake/processed/
  format: parquet
```

## Azure ADLS

### Installation

```bash
pip install quicketl[azure]
```

### Configuration

```yaml
source:
  type: file
  path: abfs://container@account.dfs.core.windows.net/data/sales.parquet
  format: parquet
```

### Authentication

#### Connection String

```bash
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;..."
```

#### Account Key

```bash
export AZURE_STORAGE_ACCOUNT_NAME=myaccount
export AZURE_STORAGE_ACCOUNT_KEY=...
```

#### Service Principal

```bash
export AZURE_TENANT_ID=...
export AZURE_CLIENT_ID=...
export AZURE_CLIENT_SECRET=...
```

### Examples

Read from Azure:

```yaml
source:
  type: file
  path: abfs://datalake@myaccount.dfs.core.windows.net/raw/sales.parquet
```

Write to Azure:

```yaml
sink:
  type: file
  path: abfs://datalake@myaccount.dfs.core.windows.net/processed/
  format: parquet
```

## URI Formats

| Provider | Format |
|----------|--------|
| AWS S3 | `s3://bucket/path/file.parquet` |
| GCS | `gs://bucket/path/file.parquet` |
| Azure ADLS Gen2 | `abfs://container@account.dfs.core.windows.net/path/file.parquet` |
| Azure Blob | `az://container/path/file.parquet` |

## Common Patterns

### Date-Partitioned Data

```yaml
source:
  type: file
  path: s3://bucket/data/year=${YEAR}/month=${MONTH}/day=${DAY}/

sink:
  type: file
  path: s3://bucket/output/${DATE}/
  partition_by: [region]
```

### Cross-Cloud Transfer

Read from one provider, write to another:

```yaml
source:
  type: file
  path: s3://source-bucket/data.parquet

sink:
  type: file
  path: gs://dest-bucket/data.parquet
```

### Environment-Specific Buckets

```yaml
source:
  type: file
  path: ${DATA_BUCKET}/raw/sales.parquet

sink:
  type: file
  path: ${OUTPUT_BUCKET}/processed/
```

```bash
# Development
export DATA_BUCKET=s3://dev-data
export OUTPUT_BUCKET=s3://dev-output

# Production
export DATA_BUCKET=s3://prod-data
export OUTPUT_BUCKET=s3://prod-output
```

## Performance Tips

### Use Parquet

Parquet files are faster to read from cloud storage due to:

- Columnar format (read only needed columns)
- Built-in compression
- Predicate pushdown support

### Regional Proximity

Place compute near your data:

- Use same region for storage and compute
- Consider multi-region buckets for global access

### Compression

Parquet is already compressed. For CSV:

```yaml
source:
  type: file
  path: s3://bucket/data.csv.gz
  format: csv
```

## Troubleshooting

### Access Denied

```
Error: Access Denied
```

- Verify credentials are set correctly
- Check bucket/object permissions
- Ensure IAM role has required permissions

### Bucket Not Found

```
Error: Bucket not found
```

- Check bucket name spelling
- Verify bucket exists in the expected region
- Check credentials have access to the bucket

### Slow Performance

- Check network connectivity
- Verify data is in the same region as compute
- Consider using larger instance types
- Use Parquet instead of CSV

### Missing Credentials

```
Error: No credentials found
```

- Set environment variables
- Configure AWS profile/GCP service account/Azure credentials
- When running locally, ensure credentials file exists

## Security Best Practices

### Use IAM Roles

Prefer IAM roles over access keys:

```yaml
# Running on AWS EC2/ECS with IAM role
source:
  type: file
  path: s3://bucket/data.parquet
  # No credentials needed - uses instance role
```

### Don't Commit Credentials

Add to `.gitignore`:

```gitignore
.env
*.json  # Service account keys
```

### Use Secrets Managers

For production, use secrets managers:

- AWS Secrets Manager
- Google Secret Manager
- Azure Key Vault

### Least Privilege

Grant minimal permissions:

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject"
  ],
  "Resource": [
    "arn:aws:s3:::my-bucket/data/*"
  ]
}
```

## Related

- [File Sources](file-sources.md) - File format options
- [File Sinks](file-sinks.md) - Writing files
- [Environment Variables](../../reference/environment-variables.md) - Credential configuration
