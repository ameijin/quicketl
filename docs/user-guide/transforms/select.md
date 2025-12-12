# select

Choose and reorder columns in your data.

## Usage

```yaml
- op: select
  columns: [id, name, amount]
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `columns` | Yes | `list[str]` | Columns to keep, in order |

## Examples

### Basic Selection

Keep only specific columns:

```yaml
# Input: id, name, email, amount, created_at, updated_at
- op: select
  columns: [id, name, amount]
# Output: id, name, amount
```

### Reorder Columns

Change column order:

```yaml
# Input: amount, id, name
- op: select
  columns: [id, name, amount]
# Output: id, name, amount
```

### Select After Transforms

Select final output columns:

```yaml
transforms:
  - op: derive_column
    name: total_with_tax
    expr: amount * 1.1

  - op: derive_column
    name: profit
    expr: amount - cost

  - op: select
    columns: [id, amount, total_with_tax, profit]
```

## Input/Output Example

**Input Data:**

| id | name | email | amount | status |
|----|------|-------|--------|--------|
| 1 | Widget A | a@example.com | 99.99 | active |
| 2 | Widget B | b@example.com | 149.99 | active |

**Transform:**

```yaml
- op: select
  columns: [id, name, amount]
```

**Output Data:**

| id | name | amount |
|----|------|--------|
| 1 | Widget A | 99.99 |
| 2 | Widget B | 149.99 |

## Python API

```python
from etlx.config.transforms import SelectTransform

transform = SelectTransform(columns=["id", "name", "amount"])
```

## Common Patterns

### Remove Sensitive Columns

```yaml
# Remove PII before output
- op: select
  columns: [id, product, amount, date]
  # Excludes: email, phone, address
```

### Prepare for Join

Select only columns needed for join:

```yaml
transforms:
  - op: select
    columns: [order_id, customer_id, amount]

  - op: join
    right: customers
    on: [customer_id]
```

### Final Output Schema

Ensure consistent output:

```yaml
transforms:
  # ... other transforms ...

  # Last transform: define output schema
  - op: select
    columns: [region, category, total_sales, order_count, avg_order_value]
```

## Performance

`select` is very efficient:

- Columnar formats (Parquet) only read selected columns
- Reduces memory usage
- Apply early in pipeline for best performance

```yaml
transforms:
  # Good: select early, reduces data for subsequent transforms
  - op: select
    columns: [id, amount, category]
  - op: filter
    predicate: amount > 100
  - op: aggregate
    group_by: [category]
    aggs:
      total: sum(amount)
```

## Tips

### Use with Parquet Sources

With Parquet files, unselected columns aren't read from disk:

```yaml
source:
  type: file
  path: large_file.parquet  # 100 columns

transforms:
  - op: select
    columns: [id, amount]   # Only reads 2 columns
```

### Column Order Matters

Columns appear in the order specified:

```yaml
- op: select
  columns: [z_col, a_col, m_col]
# Output columns: z_col, a_col, m_col
```

## Errors

### Column Not Found

```
Error: Column 'nonexistent' not found in table
```

Check that all columns in `columns` exist in the input data.

### Empty Column List

```
Error: 'columns' must not be empty
```

Provide at least one column.

## Related

- [rename](rename.md) - Rename columns
- [derive_column](derive-column.md) - Add new columns
- [aggregate](aggregate.md) - Select is often used before aggregation
