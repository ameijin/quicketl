# Basic Pipeline Example

This example demonstrates QuickETL fundamentals: reading a CSV file, applying transforms, running quality checks, and writing output.

## Overview

**Goal**: Process sales data to get completed orders with calculated totals.

**Steps**:

1. Read CSV file
2. Filter to completed orders
3. Calculate order totals
4. Validate data quality
5. Write to Parquet

## Sample Data

Create `data/sales.csv`:

```csv
id,customer_name,product,quantity,unit_price,status,order_date
1,Alice Smith,Widget A,2,29.99,completed,2025-01-15
2,Bob Johnson,Gadget B,1,49.99,pending,2025-01-15
3,Carol White,Widget A,3,29.99,completed,2025-01-16
4,David Brown,Service C,1,99.99,completed,2025-01-16
5,Eve Davis,Gadget B,2,49.99,cancelled,2025-01-17
6,Frank Miller,Widget A,5,29.99,completed,2025-01-17
7,Grace Lee,Service C,1,99.99,pending,2025-01-18
8,Henry Wilson,Gadget B,1,49.99,completed,2025-01-18
```

## Pipeline Configuration

Create `pipelines/basic.yml`:

```yaml
# Basic Pipeline Example
# Processes sales data to calculate order totals

name: basic_sales_pipeline
description: Filter completed orders and calculate totals
engine: duckdb

# Read from CSV file
source:
  type: file
  path: data/sales.csv
  format: csv

# Apply transformations
transforms:
  # Step 1: Keep only completed orders
  - op: filter
    predicate: status = 'completed'

  # Step 2: Calculate total amount for each order
  - op: derive_column
    name: total_amount
    expr: quantity * unit_price

  # Step 3: Select and reorder columns
  - op: select
    columns:
      - id
      - customer_name
      - product
      - quantity
      - unit_price
      - total_amount
      - order_date

  # Step 4: Sort by date and total
  - op: sort
    by:
      - column: order_date
        order: asc
      - column: total_amount
        order: desc

# Validate data quality
checks:
  # Ensure required fields are present
  - check: not_null
    columns: [id, customer_name, total_amount]

  # Verify we have data
  - check: row_count
    min: 1

  # Business rule: totals must be positive
  - check: expression
    expr: total_amount > 0

# Write output
sink:
  type: file
  path: output/completed_orders.parquet
  format: parquet
```

## Running the Pipeline

### Validate First

```bash
quicketl validate pipelines/basic.yml
```

Expected output:

```
Configuration is valid

Pipeline: basic_sales_pipeline
  Engine: duckdb
  Source: file (data/sales.csv)
  Transforms: 4
  Checks: 3
  Sink: file (output/completed_orders.parquet)
```

### Execute

```bash
quicketl run pipelines/basic.yml
```

Expected output:

```
Running pipeline: basic_sales_pipeline
  Filter completed orders and calculate totals
  Engine: duckdb

╭────────────────── Pipeline: basic_sales_pipeline ──────────────────╮
│ SUCCESS                                                            │
╰─────────────────────────────── Duration: 45.2ms ───────────────────╯

Steps
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
┃ Step             ┃ Type       ┃ Status ┃ Duration ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━┩
│ read_source      │ file       │ OK     │   12.1ms │
│ transform_0      │ filter     │ OK     │    0.8ms │
│ transform_1      │ derive     │ OK     │    0.3ms │
│ transform_2      │ select     │ OK     │    0.2ms │
│ transform_3      │ sort       │ OK     │    0.4ms │
│ quality_checks   │ checks     │ OK     │    5.2ms │
│ write_sink       │ file       │ OK     │    8.1ms │
└──────────────────┴────────────┴────────┴──────────┘

Quality Checks: PASSED (3/3 passed)

Rows processed: 8
Rows written: 5
```

## Expected Output

The output file `output/completed_orders.parquet` contains:

| id | customer_name | product | quantity | unit_price | total_amount | order_date |
|----|---------------|---------|----------|------------|--------------|------------|
| 1 | Alice Smith | Widget A | 2 | 29.99 | 59.98 | 2025-01-15 |
| 4 | David Brown | Service C | 1 | 99.99 | 99.99 | 2025-01-16 |
| 3 | Carol White | Widget A | 3 | 29.99 | 89.97 | 2025-01-16 |
| 6 | Frank Miller | Widget A | 5 | 29.99 | 149.95 | 2025-01-17 |
| 8 | Henry Wilson | Gadget B | 1 | 49.99 | 49.99 | 2025-01-18 |

## Verify Output

Read the output with DuckDB:

```bash
duckdb -c "SELECT * FROM 'output/completed_orders.parquet'"
```

Or with Python:

```python
import pandas as pd
df = pd.read_parquet("output/completed_orders.parquet")
print(df)
```

## Step-by-Step Breakdown

### 1. Source Configuration

```yaml
source:
  type: file
  path: data/sales.csv
  format: csv
```

- `type: file` - Read from filesystem
- `path` - File location (supports glob patterns)
- `format: csv` - File format for parsing

### 2. Filter Transform

```yaml
- op: filter
  predicate: status = 'completed'
```

- Keeps only rows where `status` equals `'completed'`
- Removes pending and cancelled orders

### 3. Derive Column

```yaml
- op: derive_column
  name: total_amount
  expr: quantity * unit_price
```

- Creates a new column `total_amount`
- Calculates value using SQL expression

### 4. Select Columns

```yaml
- op: select
  columns: [id, customer_name, product, quantity, unit_price, total_amount, order_date]
```

- Explicitly choose which columns to keep
- Defines output column order

### 5. Sort

```yaml
- op: sort
  by:
    - column: order_date
      order: asc
    - column: total_amount
      order: desc
```

- Primary sort by `order_date` ascending
- Secondary sort by `total_amount` descending

### 6. Quality Checks

```yaml
checks:
  - check: not_null
    columns: [id, customer_name, total_amount]
  - check: row_count
    min: 1
  - check: expression
    expr: total_amount > 0
```

- Ensures no NULL values in key columns
- Verifies at least 1 row output
- Validates business rule (positive totals)

## Variations

### Output to CSV

```yaml
sink:
  type: file
  path: output/completed_orders.csv
  format: csv
```

### With Variables

```yaml
source:
  type: file
  path: data/sales_${DATE}.csv
  format: csv
```

```bash
quicketl run pipelines/basic.yml --var DATE=2025-01-15
```

### Dry Run

Preview without writing output:

```bash
quicketl run pipelines/basic.yml --dry-run
```

## Next Steps

- [Multi-Source Join](multi-source-join.md) - Combine multiple data sources
- [Aggregation](aggregation.md) - Compute metrics and summaries
- [Transforms Reference](../guides/transforms/index.md) - All available transforms
