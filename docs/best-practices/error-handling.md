# Error Handling Best Practices

Strategies for handling errors gracefully in QuickETL pipelines.

## Types of Errors

### Configuration Errors

Invalid YAML or missing required fields:

```bash
$ quicketl validate pipeline.yml
Configuration is invalid

Errors:
  - sink: Field required
  - transforms -> 0 -> op: Input should be 'select', 'filter', ...
```

**Prevention**: Always validate before running:

```bash
quicketl validate pipeline.yml && quicketl run pipeline.yml
```

### Runtime Errors

Errors during execution:

- File not found
- Database connection failed
- Out of memory
- Permission denied

### Data Quality Errors

Quality checks that fail:

```
Quality Checks: FAILED (2/3 passed)
  ✓ not_null: id, name
  ✗ unique: email (152 duplicates found)
  ✓ row_count: min=1
```

## Quality Check Strategies

### Critical vs Non-Critical Checks

```yaml
checks:
  # Critical: Must pass 100%
  - check: not_null
    columns: [id, customer_id]

  - check: unique
    columns: [id]

  # Non-critical: Warning only (use threshold)
  - check: expression
    expr: email LIKE '%@%.%'
    threshold: 0.95  # 95% must pass

  - check: expression
    expr: amount > 0
    threshold: 0.99  # 99% must pass
```

### Continue on Check Failure

For non-critical pipelines:

```bash
quicketl run pipeline.yml --no-fail-on-checks
```

### Programmatic Handling

```python
from quicketl import Pipeline
from quicketl.exceptions import QualityCheckError

pipeline = Pipeline.from_yaml("pipeline.yml")

try:
    result = pipeline.run(fail_on_checks=True)
except QualityCheckError as e:
    print(f"Quality checks failed:")
    for check in e.failed_checks:
        print(f"  - {check.name}: {check.message}")

    # Decide what to do
    if "critical" in e.failed_checks[0].name:
        raise  # Re-raise for critical failures
    else:
        # Log and continue for warnings
        logger.warning(f"Non-critical check failed: {e}")
```

## Retry Strategies

### Simple Retry Script

```bash
#!/bin/bash
MAX_RETRIES=3
RETRY_DELAY=60

for i in $(seq 1 $MAX_RETRIES); do
    if quicketl run pipeline.yml --var DATE=$1; then
        echo "Success on attempt $i"
        exit 0
    fi

    if [ $i -lt $MAX_RETRIES ]; then
        echo "Attempt $i failed, retrying in ${RETRY_DELAY}s..."
        sleep $RETRY_DELAY
    fi
done

echo "Failed after $MAX_RETRIES attempts"
exit 1
```

### Exponential Backoff

```bash
#!/bin/bash
MAX_RETRIES=5
BASE_DELAY=30

for i in $(seq 1 $MAX_RETRIES); do
    if quicketl run pipeline.yml; then
        exit 0
    fi

    if [ $i -lt $MAX_RETRIES ]; then
        DELAY=$((BASE_DELAY * 2 ** (i - 1)))
        echo "Retry $i in ${DELAY}s..."
        sleep $DELAY
    fi
done

exit 1
```

### Python Retry

```python
import time
from quicketl import Pipeline
from quicketl.exceptions import ExecutionError

def run_with_retry(config_path, max_retries=3, base_delay=30):
    pipeline = Pipeline.from_yaml(config_path)

    for attempt in range(1, max_retries + 1):
        try:
            return pipeline.run()
        except ExecutionError as e:
            if attempt == max_retries:
                raise

            delay = base_delay * (2 ** (attempt - 1))
            print(f"Attempt {attempt} failed: {e}")
            print(f"Retrying in {delay}s...")
            time.sleep(delay)
```

## Logging and Monitoring

### Verbose Output

```bash
quicketl run pipeline.yml --verbose
```

Shows detailed step-by-step execution.

### JSON Output for Monitoring

```bash
quicketl run pipeline.yml --json > result.json
```

```json
{
  "pipeline_name": "daily_sales",
  "status": "SUCCESS",
  "duration_ms": 1234.5,
  "rows_processed": 10000,
  "rows_written": 9500,
  "checks_passed": 3,
  "checks_failed": 0
}
```

### Send to Monitoring System

```bash
#!/bin/bash
RESULT=$(quicketl run pipeline.yml --json)
STATUS=$(echo $RESULT | jq -r '.status')
DURATION=$(echo $RESULT | jq -r '.duration_ms')
ROWS=$(echo $RESULT | jq -r '.rows_written')

# Send to DataDog
curl -X POST "https://api.datadoghq.com/api/v1/series" \
  -H "Content-Type: application/json" \
  -H "DD-API-KEY: $DD_API_KEY" \
  -d "{
    \"series\": [{
      \"metric\": \"quicketl.pipeline.duration\",
      \"points\": [[$(date +%s), $DURATION]],
      \"tags\": [\"pipeline:daily_sales\", \"status:$STATUS\"]
    }]
  }"
```

## Error Recovery Patterns

### Idempotent Pipelines

Design pipelines that can be safely re-run:

```yaml
# Replace mode: Safe to re-run
sink:
  type: database
  connection: postgres
  table: analytics.daily_metrics
  mode: replace

# Or use merge with keys
sink:
  type: database
  connection: postgres
  table: analytics.daily_metrics
  mode: merge
  merge_keys: [date, region]  # Unique identifier
```

### Checkpoint Pattern

For long-running pipelines, break into checkpoints:

```yaml
# Step 1: Extract (can re-run)
name: extract_raw
sink:
  type: file
  path: staging/raw_${DATE}.parquet

# Step 2: Transform (starts from checkpoint)
name: transform_data
source:
  type: file
  path: staging/raw_${DATE}.parquet  # Checkpoint
sink:
  type: file
  path: staging/transformed_${DATE}.parquet

# Step 3: Load (final step)
name: load_warehouse
source:
  type: file
  path: staging/transformed_${DATE}.parquet
sink:
  type: database
  connection: snowflake
  table: analytics.metrics
```

### Dead Letter Queue

Capture failed records:

```python
from quicketl import Pipeline

pipeline = Pipeline.from_yaml("pipeline.yml")

try:
    result = pipeline.run(fail_on_checks=False)

    if result.checks_failed > 0:
        # Get failed records
        failed_df = result.get_failed_records()

        # Write to dead letter queue
        failed_df.to_parquet(f"dlq/failed_{date}.parquet")

except Exception as e:
    # Log entire batch to DLQ
    logger.error(f"Pipeline failed: {e}")
    shutil.copy(input_file, f"dlq/failed_batch_{date}.parquet")
```

## Alerting

### Email on Failure

```bash
#!/bin/bash
if ! quicketl run pipeline.yml; then
    echo "Pipeline failed at $(date)" | \
    mail -s "ALERT: ETL Pipeline Failed" team@company.com
    exit 1
fi
```

### Slack Notification

```python
import requests
from quicketl import Pipeline

SLACK_WEBHOOK = "https://hooks.slack.com/services/..."

def notify_slack(message, color="danger"):
    requests.post(SLACK_WEBHOOK, json={
        "attachments": [{
            "color": color,
            "text": message
        }]
    })

try:
    pipeline = Pipeline.from_yaml("pipeline.yml")
    result = pipeline.run()

    notify_slack(
        f"✓ Pipeline completed: {result.rows_written} rows",
        color="good"
    )
except Exception as e:
    notify_slack(f"✗ Pipeline failed: {e}")
    raise
```

### PagerDuty Integration

```bash
#!/bin/bash
if ! quicketl run pipeline.yml; then
    curl -X POST https://events.pagerduty.com/v2/enqueue \
      -H "Content-Type: application/json" \
      -d '{
        "routing_key": "'$PD_ROUTING_KEY'",
        "event_action": "trigger",
        "payload": {
          "summary": "ETL Pipeline Failed",
          "severity": "critical",
          "source": "quicketl"
        }
      }'
    exit 1
fi
```

## Debugging Tips

### Dry Run

Test without writing output:

```bash
quicketl run pipeline.yml --dry-run
```

### Verbose Logging

```bash
quicketl run pipeline.yml --verbose
```

### Validate Configuration

```bash
quicketl validate pipeline.yml --verbose
```

### Check Backend Availability

```bash
quicketl info --backends --check
```

### Test with Sample Data

Create a small test dataset:

```bash
head -100 data/large_file.csv > data/test_sample.csv
quicketl run pipeline.yml --var INPUT=data/test_sample.csv
```

## Related

- [Quality Checks](../user-guide/quality/index.md) - Check configuration
- [Production](production.md) - Production deployment
- [Troubleshooting](../reference/troubleshooting.md) - Common issues
