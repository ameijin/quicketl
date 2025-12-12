# Database Sources

Read data from relational databases using SQL queries or table references.

## Basic Usage

```yaml
source:
  type: database
  connection: postgresql://user:pass@localhost:5432/mydb
  table: sales
```

## Configuration

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `type` | Yes | - | Must be `database` |
| `connection` | Yes | - | Database connection string |
| `table` | No* | - | Table name to read |
| `query` | No* | - | SQL query to execute |

*Either `table` or `query` is required, but not both.

## Connection Strings

### PostgreSQL

```yaml
source:
  type: database
  connection: postgresql://user:password@host:5432/database
  table: sales
```

### MySQL

```yaml
source:
  type: database
  connection: mysql://user:password@host:3306/database
  table: sales
```

### SQLite

```yaml
source:
  type: database
  connection: sqlite:///path/to/database.db
  table: sales
```

### Using Environment Variables

Store connection strings securely:

```yaml
source:
  type: database
  connection: ${DATABASE_URL}
  table: sales
```

```bash
export DATABASE_URL=postgresql://user:pass@localhost/db
```

## Reading Tables

Read an entire table:

```yaml
source:
  type: database
  connection: ${DATABASE_URL}
  table: sales
```

This is equivalent to `SELECT * FROM sales`.

## Using Queries

For more control, use a SQL query:

```yaml
source:
  type: database
  connection: ${DATABASE_URL}
  query: |
    SELECT
      id,
      customer_id,
      amount,
      created_at
    FROM sales
    WHERE created_at >= '2025-01-01'
      AND status = 'completed'
```

### Complex Queries

```yaml
source:
  type: database
  connection: ${DATABASE_URL}
  query: |
    SELECT
      s.id,
      s.amount,
      c.name as customer_name,
      c.tier as customer_tier
    FROM sales s
    JOIN customers c ON s.customer_id = c.id
    WHERE s.created_at >= '2025-01-01'
```

### Parameterized Queries

Use variables in queries:

```yaml
source:
  type: database
  connection: ${DATABASE_URL}
  query: |
    SELECT *
    FROM sales
    WHERE created_at >= '${START_DATE}'
      AND created_at < '${END_DATE}'
      AND region = '${REGION}'
```

```bash
quicketl run pipeline.yml \
  --var START_DATE=2025-01-01 \
  --var END_DATE=2025-02-01 \
  --var REGION=north
```

## Supported Databases

| Database | Connection Prefix | Install Extra |
|----------|-------------------|---------------|
| PostgreSQL | `postgresql://` | `etlx[postgres]` |
| MySQL | `mysql://` | `etlx[mysql]` |
| SQLite | `sqlite:///` | Built-in |
| ClickHouse | `clickhouse://` | `etlx[clickhouse]` |
| Snowflake | See below | `etlx[snowflake]` |
| BigQuery | See below | `etlx[bigquery]` |

### Snowflake

```yaml
source:
  type: database
  connection: snowflake://user:pass@account/database/schema?warehouse=compute_wh
  table: sales
```

Or use environment variables:

```bash
export SNOWFLAKE_ACCOUNT=abc123.us-east-1
export SNOWFLAKE_USER=myuser
export SNOWFLAKE_PASSWORD=mypass
export SNOWFLAKE_DATABASE=mydb
export SNOWFLAKE_SCHEMA=public
export SNOWFLAKE_WAREHOUSE=compute_wh
```

### BigQuery

```yaml
source:
  type: database
  connection: bigquery://project-id
  query: SELECT * FROM `project.dataset.table`
```

Set credentials via environment:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

## Python API

```python
from etlx.config.models import DatabaseSource

# Using table
source = DatabaseSource(
    connection="postgresql://localhost/db",
    table="sales"
)

# Using query
source = DatabaseSource(
    connection="${DATABASE_URL}",
    query="SELECT * FROM sales WHERE amount > 100"
)
```

## Performance Tips

### Select Only Needed Columns

Instead of `SELECT *`, specify columns:

```yaml
source:
  type: database
  query: SELECT id, amount, date FROM sales
```

### Use Query Filters

Filter in the database rather than after loading:

```yaml
# Good - filters in database
source:
  type: database
  query: SELECT * FROM sales WHERE date >= '2025-01-01'

# Less efficient - loads all then filters
source:
  type: database
  table: sales
transforms:
  - op: filter
    predicate: date >= '2025-01-01'
```

### Limit Rows for Testing

```yaml
source:
  type: database
  query: SELECT * FROM sales LIMIT 1000
```

## Troubleshooting

### Connection Refused

```
Error: Connection refused
```

- Check the host and port are correct
- Verify the database server is running
- Check firewall rules

### Authentication Failed

```
Error: Authentication failed
```

- Verify username and password
- Check the user has access to the database
- For cloud databases, check credentials are configured

### Missing Driver

```
Error: No module named 'psycopg2'
```

Install the required extra:

```bash
pip install quicketl[postgres]
```

### Timeout

For long-running queries, consider:

- Adding query timeouts in your database
- Breaking into smaller queries
- Using incremental extraction patterns

## Related

- [Cloud Storage](cloud-storage.md) - Alternative to database reads
- [Database Sinks](database-sinks.md) - Writing to databases
- [Backends](../backends/index.md) - Backend-specific features
