# cast

Convert column data types.

## Usage

```yaml
- op: cast
  columns:
    id: string
    amount: float64
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `columns` | Yes | `dict[str, str]` | Column → target type mapping |

## Supported Types

| Type | Aliases | Description |
|------|---------|-------------|
| `string` | `str` | Text/string |
| `int64` | `int`, `integer` | 64-bit integer |
| `int32` | | 32-bit integer |
| `float64` | `float`, `double` | 64-bit float |
| `float32` | | 32-bit float |
| `boolean` | `bool` | True/False |
| `date` | | Date (no time) |
| `datetime` | `timestamp` | Date with time |

## Examples

### String to Number

```yaml
- op: cast
  columns:
    quantity: int64
    price: float64
```

### Number to String

```yaml
- op: cast
  columns:
    zip_code: string
    product_id: string
```

### String to Date

```yaml
- op: cast
  columns:
    order_date: date
    created_at: datetime
```

### Multiple Casts

```yaml
- op: cast
  columns:
    id: string
    quantity: int64
    amount: float64
    is_active: boolean
    created_at: datetime
```

## Input/Output Example

**Input Data:**

| id | amount | is_active |
|----|--------|-----------|
| 1 | "99.99" | "true" |
| 2 | "149.50" | "false" |

**Transform:**

```yaml
- op: cast
  columns:
    id: string
    amount: float64
    is_active: boolean
```

**Output Data:**

| id | amount | is_active |
|----|--------|-----------|
| "1" | 99.99 | true |
| "2" | 149.50 | false |

## Python API

```python
from etlx.config.transforms import CastTransform

transform = CastTransform(
    columns={
        "id": "string",
        "amount": "float64",
        "is_active": "boolean",
    }
)
```

## Common Patterns

### Prepare for Calculations

```yaml
transforms:
  # Cast strings to numbers
  - op: cast
    columns:
      quantity: int64
      price: float64

  # Now can calculate
  - op: derive_column
    name: total
    expr: quantity * price
```

### Standardize IDs

```yaml
- op: cast
  columns:
    customer_id: string
    order_id: string
    product_id: string
```

### Parse Dates

```yaml
transforms:
  - op: cast
    columns:
      date_string: date

  - op: derive_column
    name: year
    expr: extract(year from date_string)
```

## Tips

### Cast Before Join

Ensure join keys have matching types:

```yaml
transforms:
  # Orders: customer_id is integer
  - op: cast
    columns:
      customer_id: string

  # Now matches customers.customer_id (string)
  - op: join
    right: customers
    on: [customer_id]
```

### Handle Nulls

Casting preserves nulls:

```yaml
# If amount is NULL, cast result is still NULL
- op: cast
  columns:
    amount: float64
```

### Boolean Casting

Common boolean representations:

| Input | Cast to boolean |
|-------|-----------------|
| `"true"`, `"1"`, `1` | `true` |
| `"false"`, `"0"`, `0` | `false` |

## Errors

### Invalid Cast

```
Error: Cannot cast 'abc' to integer
```

Data must be convertible. Filter invalid values first:

```yaml
transforms:
  - op: filter
    predicate: amount IS NOT NULL AND amount != ''

  - op: cast
    columns:
      amount: float64
```

### Unknown Type

```
Error: Unknown type 'varchar'
```

Use supported type names. `string` instead of `varchar`.

## Related

- [derive_column](derive-column.md) - Calculate after casting
- [fill_null](fill-null.md) - Handle nulls before casting
- [Data Types](../../reference/data-types.md) - Type reference
