# Production Best Practices

Guidelines for running ETLX pipelines reliably in production environments.

## Environment Configuration

### Use Environment Variables

Never hardcode credentials or environment-specific values:

```yaml
# Good: Environment variables
source:
  type: database
  connection: ${DATABASE_CONNECTION}

sink:
  type: file
  path: ${OUTPUT_BUCKET}/data/${DATE}/
```

```bash
# Set in environment
export DATABASE_CONNECTION=postgres_prod
export OUTPUT_BUCKET=s3://prod-data-lake
export DATE=$(date +%Y-%m-%d)

quicketl run pipeline.yml
```

### Use .env Files

For local development and deployment:

```bash
# .env.production
DATABASE_URL=postgresql://user:pass@prod-db:5432/analytics
S3_BUCKET=prod-data-lake
SNOWFLAKE_ACCOUNT=xy12345.us-east-1
SNOWFLAKE_USER=etl_service
SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD}  # From secrets manager
```

### Secrets Management

**Never commit secrets to git.**

Use secret managers:

```bash
# AWS Secrets Manager
export DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id prod/quicketl/db-password \
  --query SecretString --output text)

# HashiCorp Vault
export DB_PASSWORD=$(vault kv get -field=password secret/quicketl/database)

# Google Secret Manager
export DB_PASSWORD=$(gcloud secrets versions access latest --secret=db-password)
```

## Monitoring and Observability

### Structured Logging

Use JSON output for parsing:

```bash
quicketl run pipeline.yml --json > /var/log/quicketl/$(date +%Y%m%d_%H%M%S).json
```

### Metrics Collection

```bash
#!/bin/bash
# run_pipeline.sh

START_TIME=$(date +%s)
RESULT=$(quicketl run pipeline.yml --json)
END_TIME=$(date +%s)

# Extract metrics
STATUS=$(echo $RESULT | jq -r '.status')
DURATION=$(echo $RESULT | jq -r '.duration_ms')
ROWS=$(echo $RESULT | jq -r '.rows_written')
CHECKS_PASSED=$(echo $RESULT | jq -r '.checks_passed')
CHECKS_FAILED=$(echo $RESULT | jq -r '.checks_failed')

# Send to monitoring system
send_metrics "etlx.pipeline.duration" $DURATION
send_metrics "etlx.pipeline.rows" $ROWS
send_metrics "etlx.pipeline.status" $([ "$STATUS" = "SUCCESS" ] && echo 1 || echo 0)
```

### DataDog Integration

```python
from datadog import statsd
from etlx import Pipeline

pipeline = Pipeline.from_yaml("pipeline.yml")

with statsd.timed("quicketl.pipeline.duration", tags=["pipeline:daily_sales"]):
    result = pipeline.run()

statsd.gauge("quicketl.pipeline.rows_written", result.rows_written,
             tags=["pipeline:daily_sales"])
statsd.gauge("quicketl.pipeline.checks_passed", result.checks_passed,
             tags=["pipeline:daily_sales"])
```

### Health Checks

```python
# health_check.py
from etlx import ETLXEngine

def check_backends():
    """Verify backend availability."""
    backends = ["duckdb", "postgres"]
    results = {}

    for backend in backends:
        try:
            engine = ETLXEngine(backend=backend)
            results[backend] = "healthy"
        except Exception as e:
            results[backend] = f"unhealthy: {e}"

    return results

if __name__ == "__main__":
    import json
    print(json.dumps(check_backends()))
```

## Scheduling

### Cron

```bash
# /etc/cron.d/quicketl
# Daily at 6 AM UTC
0 6 * * * quicketl /opt/quicketl/run_pipeline.sh daily_sales >> /var/log/quicketl/cron.log 2>&1

# Hourly
0 * * * * quicketl /opt/quicketl/run_pipeline.sh hourly_metrics >> /var/log/quicketl/cron.log 2>&1
```

### Systemd Timer

```ini
# /etc/systemd/system/quicketl-daily.service
[Unit]
Description=ETLX Daily Pipeline
After=network.target

[Service]
Type=oneshot
User=etlx
ExecStart=/opt/etlx/run_pipeline.sh daily_sales
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/quicketl-daily.timer
[Unit]
Description=Run ETLX Daily Pipeline

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable quicketl-daily.timer
sudo systemctl start quicketl-daily.timer
```

### Orchestrators

For complex workflows, use orchestrators:

- **Airflow**: [Airflow Integration](../integrations/airflow.md)
- **Prefect**: Task-based orchestration
- **Dagster**: Software-defined assets

## Error Handling

### Retry Logic

```bash
#!/bin/bash
# run_with_retry.sh

MAX_RETRIES=3
RETRY_DELAY=300  # 5 minutes

for i in $(seq 1 $MAX_RETRIES); do
    if quicketl run pipeline.yml --var DATE=$1; then
        echo "$(date): Pipeline succeeded on attempt $i"
        exit 0
    fi

    if [ $i -lt $MAX_RETRIES ]; then
        echo "$(date): Attempt $i failed, retrying in ${RETRY_DELAY}s..."
        sleep $RETRY_DELAY
    fi
done

echo "$(date): Pipeline failed after $MAX_RETRIES attempts"
exit 1
```

### Alerting

```bash
#!/bin/bash
# run_pipeline.sh

PIPELINE_NAME=$1
DATE=${2:-$(date +%Y-%m-%d)}

if ! quicketl run "pipelines/${PIPELINE_NAME}.yml" --var DATE=$DATE; then
    # Send alert
    curl -X POST "$SLACK_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"text\": \"🚨 Pipeline Failed: ${PIPELINE_NAME}\",
            \"attachments\": [{
                \"color\": \"danger\",
                \"fields\": [
                    {\"title\": \"Pipeline\", \"value\": \"${PIPELINE_NAME}\", \"short\": true},
                    {\"title\": \"Date\", \"value\": \"${DATE}\", \"short\": true}
                ]
            }]
        }"
    exit 1
fi
```

### PagerDuty for Critical Pipelines

```bash
if ! quicketl run critical_pipeline.yml; then
    curl -X POST https://events.pagerduty.com/v2/enqueue \
        -H "Content-Type: application/json" \
        -d "{
            \"routing_key\": \"$PAGERDUTY_KEY\",
            \"event_action\": \"trigger\",
            \"payload\": {
                \"summary\": \"Critical ETL Pipeline Failed\",
                \"severity\": \"critical\",
                \"source\": \"etlx-prod\"
            }
        }"
fi
```

## Deployment

### Docker

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install ETLX with required backends
RUN pip install etlx[duckdb,postgres,snowflake]

# Copy pipelines
COPY pipelines/ /app/pipelines/

# Run as non-root user
RUN useradd -m etlx
USER etlx

ENTRYPOINT ["etlx"]
CMD ["--help"]
```

```bash
# Build and run
docker build -t quicketl-pipelines .
docker run --env-file .env quicketl-pipelines run pipelines/daily.yml
```

### Kubernetes

```yaml
# k8s/quicketl-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: quicketl-daily-sales
spec:
  template:
    spec:
      containers:
        - name: quicketl
          image: quicketl-pipelines:latest
          command: ["quicketl", "run", "pipelines/daily_sales.yml"]
          env:
            - name: DATE
              value: "2025-01-15"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: quicketl-secrets
                  key: database-url
          resources:
            requests:
              memory: "2Gi"
              cpu: "1"
            limits:
              memory: "4Gi"
              cpu: "2"
      restartPolicy: OnFailure
  backoffLimit: 3
```

### Kubernetes CronJob

```yaml
# k8s/quicketl-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: quicketl-daily-sales
spec:
  schedule: "0 6 * * *"  # 6 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: quicketl
              image: quicketl-pipelines:latest
              command: ["quicketl", "run", "pipelines/daily_sales.yml"]
              envFrom:
                - secretRef:
                    name: quicketl-secrets
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
```

## Resource Management

### Memory Limits

For large datasets:

```bash
# Limit Python memory
export PYTHONMALLOC=malloc

# Use memory-efficient backend
quicketl run pipeline.yml --engine polars
```

### Disk Space

Clean up temporary files:

```bash
#!/bin/bash
# cleanup.sh

# Remove staging files older than 7 days
find /data/staging -type f -mtime +7 -delete

# Remove logs older than 30 days
find /var/log/quicketl -type f -mtime +30 -delete
```

### Database Connections

Use connection pooling:

```bash
# Use PgBouncer for PostgreSQL
export POSTGRES_HOST=pgbouncer.internal
export POSTGRES_PORT=6432
```

## Idempotency

Design pipelines to be safely re-runnable:

```yaml
# Use replace mode for full refresh
sink:
  type: database
  connection: postgres
  table: analytics.daily_metrics
  mode: replace

# Or use merge for incremental
sink:
  type: database
  connection: postgres
  table: analytics.daily_metrics
  mode: merge
  merge_keys: [date, region]
```

## Backup and Recovery

### Backup Before Major Changes

```bash
#!/bin/bash
# backup_and_run.sh

TABLE="analytics.daily_metrics"
BACKUP_TABLE="${TABLE}_backup_$(date +%Y%m%d)"

# Create backup
psql -c "CREATE TABLE $BACKUP_TABLE AS SELECT * FROM $TABLE;"

# Run pipeline
if ! quicketl run pipeline.yml; then
    echo "Pipeline failed, restoring from backup..."
    psql -c "TRUNCATE $TABLE; INSERT INTO $TABLE SELECT * FROM $BACKUP_TABLE;"
    exit 1
fi

# Cleanup old backups (keep last 7 days)
psql -c "DROP TABLE IF EXISTS ${TABLE}_backup_$(date -d '7 days ago' +%Y%m%d);"
```

## Production Checklist

Before deploying to production:

- [ ] All pipelines validated (`etlx validate`)
- [ ] Environment variables documented
- [ ] Secrets stored in secret manager
- [ ] Monitoring and alerting configured
- [ ] Retry logic implemented
- [ ] Backup strategy defined
- [ ] Resource limits set
- [ ] Runbook documented
- [ ] On-call rotation established

## Related

- [Error Handling](error-handling.md) - Handle failures gracefully
- [Testing](testing.md) - Test before deploying
- [Airflow Integration](../integrations/airflow.md) - Orchestration
