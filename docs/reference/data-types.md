# Data Types Reference

QuickETL supports standard data types that map to backend-specific types. This reference covers type handling across backends.

## Standard Types

| QuickETL Type | Description | Example Values |
|-----------|-------------|----------------|
| `string` | Text data | `"hello"`, `"John Doe"` |
| `int` | Integer numbers | `42`, `-100`, `1000000` |
| `float` | Floating-point numbers | `3.14`, `-0.001`, `1e10` |
| `bool` | Boolean values | `true`, `false` |
| `date` | Calendar date | `2025-01-15` |
| `timestamp` | Date and time | `2025-01-15 14:30:00` |
| `decimal` | Precise decimal | `99.99`, `1234.56789` |

## Type Mapping by Backend

### DuckDB

| QuickETL Type | DuckDB Type |
|-----------|-------------|
| `string` | `VARCHAR` |
| `int` | `BIGINT` |
| `float` | `DOUBLE` |
| `bool` | `BOOLEAN` |
| `date` | `DATE` |
| `timestamp` | `TIMESTAMP` |
| `decimal` | `DECIMAL` |

### Polars

| QuickETL Type | Polars Type |
|-----------|-------------|
| `string` | `Utf8` |
| `int` | `Int64` |
| `float` | `Float64` |
| `bool` | `Boolean` |
| `date` | `Date` |
| `timestamp` | `Datetime` |
| `decimal` | `Decimal` |

### PostgreSQL

| QuickETL Type | PostgreSQL Type |
|-----------|-----------------|
| `string` | `TEXT` / `VARCHAR` |
| `int` | `BIGINT` |
| `float` | `DOUBLE PRECISION` |
| `bool` | `BOOLEAN` |
| `date` | `DATE` |
| `timestamp` | `TIMESTAMP` |
| `decimal` | `NUMERIC` |

### Snowflake

| QuickETL Type | Snowflake Type |
|-----------|----------------|
| `string` | `VARCHAR` |
| `int` | `INTEGER` |
| `float` | `FLOAT` |
| `bool` | `BOOLEAN` |
| `date` | `DATE` |
| `timestamp` | `TIMESTAMP_NTZ` |
| `decimal` | `NUMBER` |

### BigQuery

| QuickETL Type | BigQuery Type |
|-----------|---------------|
| `string` | `STRING` |
| `int` | `INT64` |
| `float` | `FLOAT64` |
| `bool` | `BOOL` |
| `date` | `DATE` |
| `timestamp` | `TIMESTAMP` |
| `decimal` | `NUMERIC` |

### Pandas

| QuickETL Type | Pandas Type |
|-----------|-------------|
| `string` | `object` / `string` |
| `int` | `int64` |
| `float` | `float64` |
| `bool` | `bool` |
| `date` | `datetime64[ns]` |
| `timestamp` | `datetime64[ns]` |
| `decimal` | `float64` |

## Type Casting

### Cast Transform

Explicitly convert column types:

```yaml
transforms:
  - op: cast
    columns:
      id: int
      amount: float
      is_active: bool
      created_date: date
      updated_at: timestamp
```

### Supported Cast Targets

```yaml
transforms:
  - op: cast
    columns:
      # String types
      name: string
      code: varchar

      # Numeric types
      id: int
      id: integer
      id: bigint
      amount: float
      amount: double
      price: decimal

      # Boolean
      is_active: bool
      is_active: boolean

      # Date/Time
      order_date: date
      created_at: timestamp
```

### Cast in Expressions

```yaml
transforms:
  - op: derive_column
    name: amount_str
    expr: cast(amount as varchar)

  - op: derive_column
    name: year
    expr: cast(extract(year from date) as integer)
```

## Type Inference

### CSV Files

CSV files don't have type information. QuickETL infers types:

```yaml
source:
  type: file
  path: data.csv
  format: csv
  # Types are inferred from data
```

To override inference:

```yaml
source:
  type: file
  path: data.csv
  format: csv
  options:
    dtype:
      id: int
      amount: float
      date: date
```

### Parquet Files

Parquet preserves types from the schema:

```yaml
source:
  type: file
  path: data.parquet
  format: parquet
  # Types come from Parquet schema
```

### JSON Files

JSON types map naturally:

| JSON Type | QuickETL Type |
|-----------|-----------|
| `string` | `string` |
| `number` (integer) | `int` |
| `number` (decimal) | `float` |
| `boolean` | `bool` |
| `null` | NULL |
| `array` | Backend-specific |
| `object` | Backend-specific |

## NULL Handling

### NULL Values

All types can be NULL:

```yaml
transforms:
  - op: filter
    predicate: email IS NOT NULL

  - op: fill_null
    columns:
      email: "unknown@example.com"
      amount: 0
      is_active: false
```

### NULL-Safe Operations

```yaml
transforms:
  # COALESCE returns first non-NULL
  - op: derive_column
    name: display_name
    expr: coalesce(nickname, first_name, 'Anonymous')

  # NULLIF returns NULL if equal
  - op: derive_column
    name: safe_ratio
    expr: a / nullif(b, 0)
```

## Date and Time Formats

### Date Strings

Supported formats:

```
2025-01-15          # ISO date
2025/01/15          # Slash separator
01-15-2025          # US format (with config)
15-01-2025          # EU format (with config)
```

### Timestamp Strings

```
2025-01-15 14:30:00           # Date and time
2025-01-15T14:30:00           # ISO 8601
2025-01-15T14:30:00Z          # UTC
2025-01-15T14:30:00+05:00     # With timezone
```

### Date Parsing

```yaml
transforms:
  - op: derive_column
    name: parsed_date
    expr: date('2025-01-15')

  - op: derive_column
    name: parsed_timestamp
    expr: timestamp('2025-01-15 14:30:00')
```

## Numeric Precision

### Integer Types

| Type | Range |
|------|-------|
| `int` / `bigint` | -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807 |
| `int32` | -2,147,483,648 to 2,147,483,647 |
| `int16` | -32,768 to 32,767 |

### Decimal Precision

For financial calculations, use `decimal`:

```yaml
transforms:
  - op: cast
    columns:
      price: decimal  # Full precision

  - op: derive_column
    name: total
    expr: cast(quantity * price as decimal(10, 2))
```

## Boolean Representations

### In CSV Files

Common boolean representations:

| True Values | False Values |
|-------------|--------------|
| `true`, `True`, `TRUE` | `false`, `False`, `FALSE` |
| `1` | `0` |
| `yes`, `Yes`, `YES` | `no`, `No`, `NO` |
| `t`, `T` | `f`, `F` |

### Casting to Boolean

```yaml
transforms:
  - op: derive_column
    name: is_active
    expr: |
      case
        when status = 'active' then true
        else false
      end
```

## Complex Types

### Arrays (Backend-Dependent)

```yaml
# DuckDB
transforms:
  - op: derive_column
    name: first_tag
    expr: tags[1]  # Array indexing

# BigQuery
transforms:
  - op: derive_column
    name: tag_count
    expr: ARRAY_LENGTH(tags)
```

### JSON (Backend-Dependent)

```yaml
# DuckDB
transforms:
  - op: derive_column
    name: user_name
    expr: json_extract(metadata, '$.user.name')

# Snowflake
transforms:
  - op: derive_column
    name: user_name
    expr: metadata:user:name::string
```

## Type Compatibility

### Implicit Conversions

Some conversions happen automatically:

```yaml
transforms:
  # int + float = float
  - op: derive_column
    name: total
    expr: quantity + 0.5  # quantity (int) + 0.5 (float) = float

  # Comparisons work across compatible types
  - op: filter
    predicate: id = '123'  # Compares int to string (may cast)
```

### Explicit Conversions

When implicit conversion fails, use explicit cast:

```yaml
transforms:
  - op: derive_column
    name: id_str
    expr: cast(id as varchar) || '-' || category
```

## Related

- [Cast Transform](../guides/transforms/operations.md#cast) - Type conversion
- [Expressions Reference](expressions.md) - Expression syntax
- [Backend Documentation](../guides/backends/index.md) - Backend-specific types
