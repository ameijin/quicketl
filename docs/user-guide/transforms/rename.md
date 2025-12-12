# rename

Rename columns using a mapping.

## Usage

```yaml
- op: rename
  mapping:
    old_name: new_name
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `mapping` | Yes | `dict[str, str]` | Old name → new name mapping |

## Examples

### Single Column

```yaml
- op: rename
  mapping:
    cust_id: customer_id
```

### Multiple Columns

```yaml
- op: rename
  mapping:
    cust_id: customer_id
    order_amt: amount
    created: created_at
```

### Standardize Naming

```yaml
- op: rename
  mapping:
    # Database columns to snake_case
    CustomerID: customer_id
    OrderAmount: order_amount
    CreatedAt: created_at
```

## Input/Output Example

**Input Data:**

| cust_id | order_amt | dt |
|---------|-----------|-----|
| C001 | 99.99 | 2025-01-15 |

**Transform:**

```yaml
- op: rename
  mapping:
    cust_id: customer_id
    order_amt: amount
    dt: order_date
```

**Output Data:**

| customer_id | amount | order_date |
|-------------|--------|------------|
| C001 | 99.99 | 2025-01-15 |

## Python API

```python
from quicketl.config.transforms import RenameTransform

transform = RenameTransform(
    mapping={
        "cust_id": "customer_id",
        "order_amt": "amount",
    }
)
```

## Common Patterns

### Clean Source Column Names

```yaml
# From external API with messy names
- op: rename
  mapping:
    "Customer ID": customer_id
    "Order Amount (USD)": amount_usd
    "Date Created": created_at
```

### Prepare for Join

Rename to match join keys:

```yaml
# Orders table
- op: rename
  mapping:
    cid: customer_id

# Now can join with customers on customer_id
```

### Add Prefixes for Joins

```yaml
# After join, disambiguate columns
- op: rename
  mapping:
    name: customer_name
    amount: order_amount
```

## Tips

### Order Doesn't Matter

Renames are applied simultaneously:

```yaml
# This works (swap names)
- op: rename
  mapping:
    a: b
    b: a
```

### Combine with Select

Use select to keep only renamed columns:

```yaml
transforms:
  - op: rename
    mapping:
      cust_id: customer_id
      order_amt: amount

  - op: select
    columns: [customer_id, amount]
```

## Errors

### Column Not Found

```
Error: Column 'nonexistent' not found
```

Check that the source column exists.

### Duplicate Target Names

```
Error: Duplicate column name 'amount'
```

Ensure all target names are unique.

## Related

- [select](select.md) - Reorder and filter columns
- [derive_column](derive-column.md) - Add new columns
