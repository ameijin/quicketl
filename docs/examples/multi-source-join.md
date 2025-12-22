# Multi-Source Join Example

This example demonstrates how to combine data from multiple sources using joins, creating an enriched dataset from orders, customers, and products.

## Overview

**Goal**: Create an enriched order report combining:

- Order data (transactions)
- Customer data (demographics)
- Product data (catalog information)

**Output**: A denormalized table with complete order information.

## Sample Data

### Orders (`data/orders.csv`)

```csv
order_id,customer_id,product_id,quantity,order_date,status
1001,C001,P001,2,2025-01-15,completed
1002,C002,P003,1,2025-01-15,completed
1003,C001,P002,3,2025-01-16,completed
1004,C003,P001,1,2025-01-16,pending
1005,C002,P004,2,2025-01-17,completed
1006,C004,P002,1,2025-01-17,completed
1007,C001,P003,2,2025-01-18,cancelled
1008,C005,P001,4,2025-01-18,completed
```

### Customers (`data/customers.csv`)

```csv
customer_id,name,email,region,signup_date
C001,Alice Smith,alice@example.com,North,2024-06-15
C002,Bob Johnson,bob@example.com,South,2024-08-22
C003,Carol White,carol@example.com,East,2024-09-10
C004,David Brown,david@example.com,West,2024-11-05
C005,Eve Davis,eve@example.com,North,2025-01-02
```

### Products (`data/products.csv`)

```csv
product_id,name,category,unit_price,cost
P001,Widget A,Electronics,29.99,15.00
P002,Gadget B,Electronics,49.99,25.00
P003,Service C,Services,99.99,40.00
P004,Widget D,Electronics,19.99,10.00
P005,Tool E,Hardware,39.99,20.00
```

## Pipeline Configuration

Create `pipelines/order_report.yml`:

```yaml
name: enriched_order_report
description: Join orders with customer and product data
engine: duckdb

# Start with orders
source:
  type: file
  path: data/orders.csv
  format: csv

transforms:
  # Filter to completed orders only
  - op: filter
    predicate: status = 'completed'

  # Join with customers
  - op: join
    right:
      type: file
      path: data/customers.csv
      format: csv
    on: [customer_id]
    how: left

  # Join with products
  - op: join
    right:
      type: file
      path: data/products.csv
      format: csv
    on: [product_id]
    how: left

  # Calculate derived fields
  - op: derive_column
    name: line_total
    expr: quantity * unit_price

  - op: derive_column
    name: profit
    expr: quantity * (unit_price - cost)

  - op: derive_column
    name: profit_margin
    expr: (unit_price - cost) / unit_price

  # Select and rename final columns
  - op: select
    columns:
      - order_id
      - order_date
      - customer_id
      - name        # customer name from join
      - email
      - region
      - product_id
      - name        # product name - will need rename
      - category
      - quantity
      - unit_price
      - line_total
      - profit
      - profit_margin

  # Rename duplicate 'name' columns
  - op: rename
    columns:
      name: product_name
      name_1: customer_name

  # Sort by order date
  - op: sort
    by:
      - column: order_date
        order: desc
      - column: order_id
        order: asc

# Quality checks
checks:
  - type: not_null
    columns: [order_id, customer_id, product_id, line_total]

  - type: expression
    expr: line_total > 0

  - type: expression
    expr: profit_margin >= 0 AND profit_margin <= 1

# Write enriched data
sink:
  type: file
  path: output/order_report.parquet
  format: parquet
```

## Alternative: Explicit Column Selection

To avoid column name conflicts, use explicit selection:

```yaml
transforms:
  # Join with customers
  - op: join
    right:
      type: file
      path: data/customers.csv
      format: csv
    on: [customer_id]
    how: left

  # Rename immediately after join
  - op: rename
    columns:
      name: customer_name

  # Join with products
  - op: join
    right:
      type: file
      path: data/products.csv
      format: csv
    on: [product_id]
    how: left

  # Rename product name
  - op: rename
    columns:
      name: product_name
```

## Running the Pipeline

```bash
# Validate
quicketl validate pipelines/order_report.yml

# Execute
quicketl run pipelines/order_report.yml
```

## Expected Output

| order_id | order_date | customer_name | region | product_name | category | quantity | line_total | profit | profit_margin |
|----------|------------|---------------|--------|--------------|----------|----------|------------|--------|---------------|
| 1008 | 2025-01-18 | Eve Davis | North | Widget A | Electronics | 4 | 119.96 | 59.96 | 0.50 |
| 1006 | 2025-01-17 | David Brown | West | Gadget B | Electronics | 1 | 49.99 | 24.99 | 0.50 |
| 1005 | 2025-01-17 | Bob Johnson | South | Widget D | Electronics | 2 | 39.98 | 19.98 | 0.50 |
| 1003 | 2025-01-16 | Alice Smith | North | Gadget B | Electronics | 3 | 149.97 | 74.97 | 0.50 |
| 1002 | 2025-01-15 | Bob Johnson | South | Service C | Services | 1 | 99.99 | 59.99 | 0.60 |
| 1001 | 2025-01-15 | Alice Smith | North | Widget A | Electronics | 2 | 59.98 | 29.98 | 0.50 |

## Join Types Explained

### Inner Join

Only matching rows from both tables:

```yaml
- op: join
  right: ...
  on: [customer_id]
  how: inner  # Only orders with matching customers
```

### Left Join

All rows from left table, matching from right:

```yaml
- op: join
  right: ...
  on: [customer_id]
  how: left  # All orders, customer data where available
```

### Right Join

All rows from right table, matching from left:

```yaml
- op: join
  right: ...
  on: [customer_id]
  how: right  # All customers, their orders where available
```

### Outer Join

All rows from both tables:

```yaml
- op: join
  right: ...
  on: [customer_id]
  how: outer  # All orders and all customers
```

## Multiple Join Keys

For composite keys:

```yaml
- op: join
  right:
    type: file
    path: data/inventory.csv
    format: csv
  on: [product_id, warehouse_id]  # Multiple columns
  how: inner
```

## Handling Missing Data

After a left join, the right side may have NULLs:

```yaml
transforms:
  - op: join
    right: ...
    on: [customer_id]
    how: left

  # Fill NULL values from failed joins
  - op: fill_null
    columns:
      customer_name: Unknown Customer
      region: Unknown
```

## Performance Tips

### 1. Filter Before Joining

Reduce data volume before expensive joins:

```yaml
transforms:
  # Filter first
  - op: filter
    predicate: status = 'completed' AND order_date >= '2025-01-01'

  # Then join (fewer rows to process)
  - op: join
    right: ...
```

### 2. Join Smaller Tables

Put larger table on the left, smaller on right:

```yaml
# Good: Large orders table on left
source:
  type: file
  path: data/orders.csv  # 1M rows

transforms:
  - op: join
    right:
      type: file
      path: data/products.csv  # 1K rows (smaller)
```

### 3. Select Only Needed Columns

Reduce memory by selecting early:

```yaml
transforms:
  - op: join
    right:
      type: file
      path: data/customers.csv
      format: csv
    on: [customer_id]
    how: left

  # Select immediately after join
  - op: select
    columns: [order_id, customer_id, name, region]
```

## Next Steps

- [Aggregation Example](aggregation.md) - Compute metrics from joined data
- [Join Transform Reference](../guides/transforms/operations.md#join) - Full documentation
- [Performance Best Practices](../best-practices/performance.md)
