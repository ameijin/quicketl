# join

Join two datasets on one or more columns.

## Usage

```yaml
- op: join
  right: customers
  on: [customer_id]
  how: left
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `right` | Yes | - | Reference to right dataset |
| `on` | Yes | - | Join key columns |
| `how` | No | `inner` | Join type: `inner`, `left`, `right`, `outer` |

## Join Types

| Type | Description |
|------|-------------|
| `inner` | Only matching rows from both sides |
| `left` | All rows from left, matching from right |
| `right` | All rows from right, matching from left |
| `outer` | All rows from both sides |

## Examples

### Inner Join

```yaml
- op: join
  right: customers
  on: [customer_id]
  how: inner
```

### Left Join

```yaml
- op: join
  right: customers
  on: [customer_id]
  how: left
```

### Multiple Join Keys

```yaml
- op: join
  right: products
  on: [product_id, region]
  how: left
```

## Input/Output Example

**Orders (left):**

| order_id | customer_id | amount |
|----------|-------------|--------|
| 1 | C001 | 100 |
| 2 | C002 | 200 |
| 3 | C003 | 150 |

**Customers (right):**

| customer_id | name | tier |
|-------------|------|------|
| C001 | Acme | Gold |
| C002 | Globex | Silver |

**Left Join:**

```yaml
- op: join
  right: customers
  on: [customer_id]
  how: left
```

**Output:**

| order_id | customer_id | amount | name | tier |
|----------|-------------|--------|------|------|
| 1 | C001 | 100 | Acme | Gold |
| 2 | C002 | 200 | Globex | Silver |
| 3 | C003 | 150 | NULL | NULL |

## Python API

```python
from quicketl.config.transforms import JoinTransform

transform = JoinTransform(
    right="customers",
    on=["customer_id"],
    how="left"
)
```

## Multi-Source Pipeline

For joins, you need multiple sources. Use Python API:

```python
from quicketl import Pipeline, QuickETLEngine
from quicketl.config.models import FileSource

engine = QuickETLEngine(backend="duckdb")

# Read both datasets
orders = engine.read_file("orders.parquet", "parquet")
customers = engine.read_file("customers.parquet", "parquet")

# Join
result = engine.join(
    left=orders,
    right=customers,
    on=["customer_id"],
    how="left"
)
```

## Common Patterns

### Enrich with Dimensions

```yaml
transforms:
  - op: join
    right: customers
    on: [customer_id]
    how: left

  - op: join
    right: products
    on: [product_id]
    how: left
```

### Validate Referential Integrity

Use inner join to find orphans:

```python
# Find orders without matching customers
inner_count = engine.row_count(
    engine.join(orders, customers, ["customer_id"], "inner")
)
left_count = engine.row_count(orders)

orphans = left_count - inner_count
```

### Star Schema Join

```yaml
# Join fact table with dimensions
transforms:
  - op: join
    right: dim_customer
    on: [customer_id]
    how: left

  - op: join
    right: dim_product
    on: [product_id]
    how: left

  - op: join
    right: dim_date
    on: [date_id]
    how: left
```

## Tips

### Column Naming

After join, columns from both tables are included. Watch for name conflicts:

```yaml
transforms:
  - op: join
    right: customers
    on: [customer_id]

  # Rename to avoid confusion
  - op: rename
    mapping:
      name: customer_name
```

### Join Key Types

Ensure join keys have matching types:

```yaml
transforms:
  # Cast to match types
  - op: cast
    columns:
      customer_id: string

  - op: join
    right: customers
    on: [customer_id]
```

### Performance

- Join on indexed columns when possible
- Filter before joining to reduce data
- Consider join order (smaller table as right)

## Errors

### Column Not Found

```
Error: Join column 'cust_id' not found
```

Verify the join column exists in both datasets.

### Type Mismatch

```
Error: Cannot join on columns with different types
```

Cast columns to matching types before joining.

## Related

- [cast](cast.md) - Match types for join
- [rename](rename.md) - Rename after join
- [select](select.md) - Select columns after join
