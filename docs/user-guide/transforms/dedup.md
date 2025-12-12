# dedup

Remove duplicate rows.

## Usage

```yaml
- op: dedup
  columns: [customer_id]
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `columns` | No | All columns | Columns to consider for uniqueness |

## Examples

### Deduplicate on All Columns

```yaml
# Remove exact duplicate rows
- op: dedup
```

### Deduplicate on Specific Columns

```yaml
# Keep first row for each customer_id
- op: dedup
  columns: [customer_id]
```

### Composite Key

```yaml
# Unique combination of customer and product
- op: dedup
  columns: [customer_id, product_id]
```

## Input/Output Example

**Input Data:**

| id | customer_id | product | amount |
|----|-------------|---------|--------|
| 1 | C001 | Widget | 100 |
| 2 | C001 | Gadget | 200 |
| 3 | C002 | Widget | 150 |
| 4 | C001 | Other | 50 |

**Transform:**

```yaml
- op: dedup
  columns: [customer_id]
```

**Output Data (keeps first occurrence):**

| id | customer_id | product | amount |
|----|-------------|---------|--------|
| 1 | C001 | Widget | 100 |
| 3 | C002 | Widget | 150 |

## Python API

```python
from quicketl.config.transforms import DedupTransform

# All columns
transform = DedupTransform()

# Specific columns
transform = DedupTransform(columns=["customer_id"])
```

## Common Patterns

### Remove Exact Duplicates

```yaml
# From data with duplicate rows
- op: dedup
```

### Latest Record Per Entity

```yaml
transforms:
  # Sort to get latest first
  - op: sort
    by: [updated_at]
    descending: true

  # Keep only first (latest) per customer
  - op: dedup
    columns: [customer_id]
```

### Unique Combinations

```yaml
# Unique customer-product pairs
- op: dedup
  columns: [customer_id, product_id]
```

### Clean Event Data

```yaml
transforms:
  # Remove duplicate events
  - op: dedup
    columns: [event_id]

  # Or based on combination
  - op: dedup
    columns: [user_id, event_type, timestamp]
```

## Tips

### Row Selection

When duplicates exist, the first row encountered is kept. To control which row:

```yaml
transforms:
  # Sort first to define "first"
  - op: sort
    by: [priority, created_at]
    descending: true

  - op: dedup
    columns: [customer_id]
```

### Count Duplicates

To count duplicates before removing:

```python
total_rows = engine.row_count(data)
deduped = engine.dedup(data, ["customer_id"])
deduped_rows = engine.row_count(deduped)
duplicate_count = total_rows - deduped_rows
```

### Performance

Deduplication requires comparing rows. For large datasets:

- Dedup on fewer columns is faster
- Filter first to reduce data volume

## Errors

### Column Not Found

```
Error: Column 'nonexistent' not found
```

Check that specified columns exist.

## Related

- [sort](sort.md) - Sort before dedup to control which row is kept
- [unique check](../quality/unique.md) - Verify uniqueness
- [filter](filter.md) - Alternative for removing unwanted rows
