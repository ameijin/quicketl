# MySQL Backend

MySQL is a widely-used open-source relational database. ETLX supports MySQL as both a data source and sink.

## Installation

```bash
pip install etlx[mysql]
# or
uv add etlx[mysql]
```

## When to Use MySQL

**Ideal for:**

- Data already in MySQL
- OLTP workloads with ETL
- Integration with existing MySQL infrastructure
- Web application databases

**Consider alternatives when:**

- Heavy analytics workloads (use DuckDB or columnar DBs)
- Complex window functions needed
- Large-scale data warehousing

## Configuration

### Connection Setup

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=etlx_user
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=analytics
```

### Using `.env`

```
MYSQL_HOST=db.example.com
MYSQL_PORT=3306
MYSQL_USER=etlx_user
MYSQL_PASSWORD=${MYSQL_PASSWORD}
MYSQL_DATABASE=analytics
```

### Basic Pipeline

```yaml
name: mysql_etl
engine: mysql

source:
  type: database
  connection: mysql
  table: raw_transactions

transforms:
  - op: filter
    predicate: transaction_date >= '2025-01-01'
  - op: aggregate
    group_by: [customer_id]
    aggregations:
      total_amount: sum(amount)

sink:
  type: database
  connection: mysql
  table: customer_totals
  mode: replace
```

## Supported Features

### Transforms

| Transform | Support | MySQL SQL |
|-----------|---------|-----------|
| select | Full | `SELECT` |
| rename | Full | `AS alias` |
| filter | Full | `WHERE` |
| derive_column | Full | Expressions |
| cast | Full | `CAST()` |
| fill_null | Full | `COALESCE()` / `IFNULL()` |
| dedup | Full | `GROUP BY` with aggregation |
| sort | Full | `ORDER BY` |
| join | Full | `JOIN` |
| aggregate | Full | `GROUP BY` |
| union | Full | `UNION ALL` |
| limit | Full | `LIMIT` |

### Data Types

| ETLX Type | MySQL Type |
|-----------|------------|
| string | VARCHAR / TEXT |
| int | INT / BIGINT |
| float | DOUBLE |
| bool | TINYINT(1) |
| date | DATE |
| timestamp | DATETIME |
| decimal | DECIMAL |

## Reading Data

### From Tables

```yaml
source:
  type: database
  connection: mysql
  table: database.table_name
```

### From Queries

```yaml
source:
  type: database
  connection: mysql
  query: |
    SELECT o.*, c.name as customer_name
    FROM orders o
    INNER JOIN customers c ON o.customer_id = c.id
    WHERE o.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
```

## Writing Data

### Replace Mode

```yaml
sink:
  type: database
  connection: mysql
  table: output_table
  mode: replace  # TRUNCATE + INSERT
```

### Append Mode

```yaml
sink:
  type: database
  connection: mysql
  table: output_table
  mode: append
```

### Upsert Mode

```yaml
sink:
  type: database
  connection: mysql
  table: output_table
  mode: upsert
  upsert_keys: [id]
```

Uses `INSERT ... ON DUPLICATE KEY UPDATE`.

## Performance Tips

### 1. Use Indexes

```sql
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_customer ON orders(customer_id);
```

### 2. Batch Inserts

Configure batch size for large writes:

```yaml
sink:
  type: database
  connection: mysql
  table: output_table
  options:
    batch_size: 5000
```

### 3. Disable Foreign Key Checks for Bulk Loads

```yaml
sink:
  type: database
  connection: mysql
  table: output_table
  mode: replace
  options:
    disable_foreign_keys: true
```

## Example: ETL Pipeline

```yaml
name: sales_summary
description: Aggregate daily sales
engine: mysql

source:
  type: database
  connection: mysql
  query: |
    SELECT
      s.sale_id,
      s.product_id,
      p.category,
      s.quantity,
      s.unit_price,
      s.sale_date
    FROM sales s
    JOIN products p ON s.product_id = p.id
    WHERE s.sale_date >= CURDATE() - INTERVAL 7 DAY

transforms:
  - op: derive_column
    name: sale_amount
    expr: quantity * unit_price

  - op: aggregate
    group_by: [category, sale_date]
    aggregations:
      total_sales: sum(sale_amount)
      total_quantity: sum(quantity)
      order_count: count(*)

sink:
  type: database
  connection: mysql
  table: sales_summary
  mode: replace
```

## Limitations

1. **Window Functions**: Limited compared to PostgreSQL
2. **CTEs**: Supported in MySQL 8.0+ only
3. **JSON**: Less mature than PostgreSQL
4. **Concurrent Writes**: Table-level locking in MyISAM

## Troubleshooting

### Connection Refused

```
mysql.connector.errors.InterfaceError: 2003: Can't connect to MySQL server
```

**Solutions**:
1. Verify MySQL is running
2. Check host and port
3. Verify `bind-address` in MySQL config

### Access Denied

```
Access denied for user 'etlx_user'@'host'
```

**Solution**:
```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON database.* TO 'etlx_user'@'%';
FLUSH PRIVILEGES;
```

### Character Set Issues

```
Incorrect string value for column
```

**Solution**: Use UTF-8:
```bash
export MYSQL_CHARSET=utf8mb4
```

## Related

- [Backend Selection](index.md) - Choosing the right backend
- [Database Sources](../io/database-sources.md) - Database configuration
- [Database Sinks](../io/database-sinks.md) - Writing to databases
