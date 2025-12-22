# Transform Operations

This page documents all transform operations available in QuickETL.

## Quick Reference

### Core Transforms

| Transform | Purpose | Example |
|-----------|---------|---------|
| [`select`](#select) | Choose and reorder columns | `columns: [id, name, amount]` |
| [`rename`](#rename) | Rename columns | `mapping: {old: new}` |
| [`filter`](#filter) | Filter rows | `predicate: amount > 100` |
| [`derive_column`](#derive_column) | Add computed columns | `expr: amount * 1.1` |
| [`cast`](#cast) | Convert types | `columns: {id: string}` |
| [`fill_null`](#fill_null) | Replace nulls | `columns: {status: "unknown"}` |
| [`dedup`](#dedup) | Remove duplicates | `columns: [customer_id]` |
| [`sort`](#sort) | Order rows | `by: [amount]` |
| [`join`](#join) | Join datasets | `on: [customer_id]` |
| [`aggregate`](#aggregate) | Group and summarize | `aggs: {total: sum(amount)}` |
| [`union`](#union) | Combine datasets | `sources: [data1, data2]` |
| [`limit`](#limit) | Limit rows | `n: 1000` |

### Advanced Transforms

| Transform | Purpose | Example |
|-----------|---------|---------|
| [`window`](#window) | Window functions | `func: row_number, partition_by: [id]` |
| [`pivot`](#pivot) | Reshape long to wide | `columns: category, values: amount` |
| [`unpivot`](#unpivot) | Reshape wide to long | `value_vars: [jan, feb, mar]` |
| [`hash_key`](#hash_key) | Generate hash keys | `columns: [id, name], algorithm: md5` |
| [`coalesce`](#coalesce) | First non-null value | `columns: [email1, email2]` |

### AI Transforms

| Transform | Purpose | Example |
|-----------|---------|---------|
| [`chunk`](#chunk) | Split text into chunks | `strategy: recursive, chunk_size: 512` |
| [`embed`](#embed) | Generate embeddings | `provider: openai, model: text-embedding-3-small` |

---

## select {#select}

Choose and reorder columns in your data.

### Usage

```yaml
- op: select
  columns: [id, name, amount]
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `columns` | Yes | `list[str]` | Columns to keep, in order |

### Examples

```yaml
# Keep specific columns
- op: select
  columns: [id, name, amount]

# Reorder columns
- op: select
  columns: [amount, id, name]

# Select after transforms for final output
- op: select
  columns: [region, total_sales, order_count]
```

### Python API

```python
from quicketl.config.transforms import SelectTransform
transform = SelectTransform(columns=["id", "name", "amount"])
```

---

## rename {#rename}

Rename columns using a mapping.

### Usage

```yaml
- op: rename
  mapping:
    old_name: new_name
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `mapping` | Yes | `dict[str, str]` | Old name → new name mapping |

### Examples

```yaml
# Single column
- op: rename
  mapping:
    cust_id: customer_id

# Multiple columns
- op: rename
  mapping:
    cust_id: customer_id
    order_amt: amount
    created: created_at
```

### Python API

```python
from quicketl.config.transforms import RenameTransform
transform = RenameTransform(mapping={"cust_id": "customer_id", "order_amt": "amount"})
```

---

## filter {#filter}

Filter rows based on a SQL-like predicate.

### Usage

```yaml
- op: filter
  predicate: amount > 100
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `predicate` | Yes | `str` | SQL-like boolean expression |

### Examples

```yaml
# Simple comparison
- op: filter
  predicate: amount > 100

# Multiple conditions
- op: filter
  predicate: amount > 100 AND status = 'active'

# OR conditions
- op: filter
  predicate: region = 'north' OR region = 'south'

# Null handling
- op: filter
  predicate: email IS NOT NULL

# Date filtering with variables
- op: filter
  predicate: created_at >= '${START_DATE}' AND created_at < '${END_DATE}'

# IN operator
- op: filter
  predicate: category IN ('Electronics', 'Home', 'Office')

# Pattern matching
- op: filter
  predicate: name LIKE 'Widget%'
```

### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=`, `!=`, `<>` | Equality | `status = 'active'` |
| `>`, `<`, `>=`, `<=` | Comparison | `amount > 100` |
| `AND`, `OR`, `NOT` | Logical | `a > 1 AND b < 10` |
| `IS NULL`, `IS NOT NULL` | Null check | `email IS NOT NULL` |
| `IN`, `NOT IN` | List membership | `region IN ('north', 'south')` |
| `BETWEEN` | Range | `amount BETWEEN 100 AND 500` |
| `LIKE` | Pattern match | `name LIKE 'Widget%'` |

### Python API

```python
from quicketl.config.transforms import FilterTransform
transform = FilterTransform(predicate="amount > 100 AND status = 'active'")
```

---

## derive_column {#derive_column}

Create a new computed column from an expression.

### Usage

```yaml
- op: derive_column
  name: total_with_tax
  expr: amount * 1.1
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `name` | Yes | `str` | Name for the new column |
| `expr` | Yes | `str` | SQL-like expression |

### Examples

```yaml
# Arithmetic
- op: derive_column
  name: total_with_tax
  expr: amount * 1.1

- op: derive_column
  name: profit_margin
  expr: (revenue - cost) / revenue * 100

# String operations
- op: derive_column
  name: full_name
  expr: concat(first_name, ' ', last_name)

# Date extraction
- op: derive_column
  name: year
  expr: extract(year from created_at)

# Conditional logic
- op: derive_column
  name: size_category
  expr: |
    CASE
      WHEN amount < 100 THEN 'small'
      WHEN amount < 1000 THEN 'medium'
      ELSE 'large'
    END

# Null handling
- op: derive_column
  name: discount_safe
  expr: COALESCE(discount, 0)
```

### Functions

| Category | Functions |
|----------|-----------|
| String | `upper()`, `lower()`, `trim()`, `concat()`, `substring()`, `length()` |
| Math | `abs()`, `round()`, `floor()`, `ceil()` |
| Date | `extract()`, `date_trunc()` |
| Null | `COALESCE()`, `NULLIF()` |

### Python API

```python
from quicketl.config.transforms import DeriveColumnTransform
transform = DeriveColumnTransform(name="total_with_tax", expr="amount * 1.1")
```

---

## cast {#cast}

Convert column data types.

### Usage

```yaml
- op: cast
  columns:
    id: string
    amount: float64
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `columns` | Yes | `dict[str, str]` | Column → target type mapping |

### Supported Types

| Type | Aliases | Description |
|------|---------|-------------|
| `string` | `str` | Text/string |
| `int64` | `int`, `integer` | 64-bit integer |
| `float64` | `float`, `double` | 64-bit float |
| `boolean` | `bool` | True/False |
| `date` | | Date (no time) |
| `datetime` | `timestamp` | Date with time |

### Examples

```yaml
# String to numbers
- op: cast
  columns:
    quantity: int64
    price: float64

# Numbers to strings
- op: cast
  columns:
    zip_code: string
    product_id: string

# String to date
- op: cast
  columns:
    order_date: date
    created_at: datetime
```

### Python API

```python
from quicketl.config.transforms import CastTransform
transform = CastTransform(columns={"id": "string", "amount": "float64"})
```

---

## fill_null {#fill_null}

Replace null values with specified defaults.

### Usage

```yaml
- op: fill_null
  columns:
    amount: 0
    status: "unknown"
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `columns` | Yes | `dict[str, any]` | Column → replacement value |

### Examples

```yaml
# Numeric defaults
- op: fill_null
  columns:
    amount: 0
    discount: 0.0
    quantity: 1

# String defaults
- op: fill_null
  columns:
    status: "unknown"
    category: "uncategorized"

# Mixed types
- op: fill_null
  columns:
    amount: 0
    status: "pending"
    is_active: true
```

### Python API

```python
from quicketl.config.transforms import FillNullTransform
transform = FillNullTransform(columns={"amount": 0, "status": "unknown"})
```

---

## dedup {#dedup}

Remove duplicate rows.

### Usage

```yaml
- op: dedup
  columns: [customer_id]
```

### Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `columns` | No | All columns | Columns to consider for uniqueness |

### Examples

```yaml
# Remove exact duplicates
- op: dedup

# Keep first per customer
- op: dedup
  columns: [customer_id]

# Unique combination
- op: dedup
  columns: [customer_id, product_id]
```

### Common Pattern: Latest Record

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

### Python API

```python
from quicketl.config.transforms import DedupTransform
transform = DedupTransform(columns=["customer_id"])
```

---

## sort {#sort}

Order rows by one or more columns.

### Usage

```yaml
- op: sort
  by: [amount]
  descending: true
```

### Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `by` | Yes | - | Columns to sort by |
| `descending` | No | `false` | Sort in descending order |

### Examples

```yaml
# Ascending
- op: sort
  by: [name]

# Descending
- op: sort
  by: [amount]
  descending: true

# Multiple columns
- op: sort
  by: [category, amount]
  descending: true
```

### Python API

```python
from quicketl.config.transforms import SortTransform
transform = SortTransform(by=["amount"], descending=True)
```

---

## join {#join}

Join two datasets on one or more columns.

!!! note "Multi-Source Pipeline Required"
    Join requires a multi-source pipeline configuration with named `sources`.

### Usage

```yaml
name: orders_with_customers
engine: duckdb

# Define named sources for join
sources:
  orders:
    type: file
    path: data/orders.parquet
  customers:
    type: file
    path: data/customers.parquet

transforms:
  - op: join
    right: customers
    "on": [customer_id]  # Note: "on" must be quoted (YAML reserved word)
    how: left

sink:
  type: file
  path: output/enriched_orders.parquet
```

### Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `right` | Yes | - | Name of the source to join with (from `sources` dict) |
| `on` | Yes | - | Join key columns (must be quoted: `"on"`) |
| `how` | No | `inner` | Join type: `inner`, `left`, `right`, `outer` |

!!! warning "YAML Reserved Word"
    The `on` parameter must be quoted as `"on"` because `on` is a reserved word in YAML (parsed as boolean `true`).

### Join Types

| Type | Description |
|------|-------------|
| `inner` | Only matching rows from both sides |
| `left` | All rows from left, matching from right |
| `right` | All rows from right, matching from left |
| `outer` | All rows from both sides |

### Examples

```yaml
# Full pipeline with left join
name: enrich_orders
engine: duckdb

sources:
  orders:
    type: file
    path: data/orders.parquet
  customers:
    type: file
    path: data/customers.parquet

transforms:
  - op: join
    right: customers
    "on": [customer_id]
    how: left
  - op: select
    columns: [order_id, customer_id, customer_name, amount]

sink:
  type: file
  path: output/enriched_orders.parquet
```

```yaml
# Multiple join keys
- op: join
  right: products
  "on": [product_id, region]
  how: inner
```

### Python API

```python
from quicketl.config.transforms import JoinTransform
transform = JoinTransform(right="customers", on=["customer_id"], how="left")
```

---

## aggregate {#aggregate}

Group data and compute summary statistics.

### Usage

```yaml
- op: aggregate
  group_by: [region]
  aggs:
    total_sales: sum(amount)
    order_count: count(*)
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `group_by` | Yes | `list[str]` | Columns to group by |
| `aggs` | Yes | `dict[str, str]` | Output column → aggregation expression |

### Aggregation Functions

| Function | Description | Example |
|----------|-------------|---------|
| `sum(col)` | Sum of values | `sum(amount)` |
| `avg(col)` / `mean(col)` | Average (mean) | `avg(amount)` |
| `min(col)` | Minimum value | `min(amount)` |
| `max(col)` | Maximum value | `max(amount)` |
| `count(*)` | Count all rows | `count(*)` |
| `count(col)` | Count non-null | `count(customer_id)` |
| `count_distinct(col)` / `nunique(col)` | Count unique values | `count_distinct(user_id)` |
| `first(col)` | First value in group | `first(name)` |
| `last(col)` | Last value in group | `last(status)` |
| `stddev(col)` / `std(col)` | Standard deviation | `stddev(amount)` |
| `variance(col)` / `var(col)` | Variance | `variance(amount)` |
| `median(col)` | Median value | `median(amount)` |
| `any(col)` / `arbitrary(col)` | Any value from group | `any(category)` |
| `collect(col)` / `collect_list(col)` | Collect values into list | `collect(tag)` |

### Examples

```yaml
# Basic aggregation
- op: aggregate
  group_by: [category]
  aggs:
    total_sales: sum(amount)

# Multiple aggregations
- op: aggregate
  group_by: [region]
  aggs:
    total_sales: sum(amount)
    avg_order: avg(amount)
    min_order: min(amount)
    max_order: max(amount)
    order_count: count(*)

# Multiple group columns
- op: aggregate
  group_by: [region, category, year]
  aggs:
    total: sum(amount)
```

### Python API

```python
from quicketl.config.transforms import AggregateTransform
transform = AggregateTransform(
    group_by=["region"],
    aggs={"total_sales": "sum(amount)", "order_count": "count(*)"}
)
```

---

## union {#union}

Vertically combine multiple datasets.

!!! note "Multi-Source Pipeline Required"
    Union requires a multi-source pipeline configuration with named `sources`.

### Usage

```yaml
name: combined_sales
engine: duckdb

# Define named sources for union
sources:
  north_sales:
    type: file
    path: data/north_sales.parquet
  south_sales:
    type: file
    path: data/south_sales.parquet

transforms:
  # Transforms before union apply to the first source (north_sales)
  - op: filter
    predicate: amount > 0
  # Union adds rows from the named sources
  - op: union
    sources: [south_sales]

sink:
  type: file
  path: output/all_sales.parquet
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `sources` | Yes | `list[str]` | Names of sources to union with (from `sources` dict) |

### Examples

```yaml
# Full pipeline combining regional data
name: combine_regions
engine: duckdb

sources:
  north:
    type: file
    path: data/north.parquet
  south:
    type: file
    path: data/south.parquet
  east:
    type: file
    path: data/east.parquet

transforms:
  - op: union
    sources: [south, east]
  - op: dedup
    columns: [order_id]
  - op: sort
    by: [created_at]
    descending: true

sink:
  type: file
  path: output/all_regions.parquet
```

!!! note "Schema Requirement"
    All datasets must have the same columns (names and types).

### Python API

```python
from quicketl.config.transforms import UnionTransform
transform = UnionTransform(sources=["south_sales", "east_sales"])
```

---

## limit {#limit}

Limit output to the first N rows.

### Usage

```yaml
- op: limit
  n: 1000
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `n` | Yes | `int` | Maximum number of rows (must be > 0) |

### Examples

```yaml
# Basic limit
- op: limit
  n: 100

# Top N pattern (with sort)
transforms:
  - op: sort
    by: [sales]
    descending: true
  - op: limit
    n: 10

# Sample for development
- op: limit
  n: ${SAMPLE_SIZE:-10000}
```

### Python API

```python
from quicketl.config.transforms import LimitTransform
transform = LimitTransform(n=1000)
```

---

## Best Practices

### Filter Early

Apply filters as early as possible to reduce data volume:

```yaml
transforms:
  - op: filter
    predicate: date >= '2025-01-01'  # First: reduce rows
  - op: derive_column
    name: metric
    expr: expensive_calculation      # Then: compute on smaller dataset
```

### Select Before Aggregate

Remove unnecessary columns before aggregation:

```yaml
transforms:
  - op: select
    columns: [category, amount]      # Remove unused columns
  - op: aggregate
    group_by: [category]
    aggs:
      total: sum(amount)
```

### Derive Before Aggregate

Create columns needed for aggregation:

```yaml
transforms:
  - op: derive_column
    name: net_amount
    expr: amount - discount
  - op: aggregate
    group_by: [region]
    aggs:
      total_net: sum(net_amount)
```

---

## window {#window}

Apply window functions over partitions.

### Usage

```yaml
- op: window
  columns:
    - name: row_num
      func: row_number
      partition_by: [customer_id]
      order_by: [order_date]
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `columns` | Yes | `list` | Window column specifications |

Each column specification:

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `name` | Yes | `str` | Output column name |
| `func` | Yes | `str` | Window function |
| `column` | No | `str` | Source column (for aggregates) |
| `partition_by` | No | `list[str]` | Partition columns |
| `order_by` | No | `list` | Order columns |
| `offset` | No | `int` | Offset for lag/lead (default: 1) |
| `default` | No | `any` | Default for lag/lead |

### Supported Functions

| Function | Description | Requires `column` |
|----------|-------------|-------------------|
| `row_number` | Sequential row number | No |
| `rank` | Rank with gaps | No |
| `dense_rank` | Rank without gaps | No |
| `lag` | Previous row value | Yes |
| `lead` | Next row value | Yes |
| `sum` | Running sum | Yes |
| `avg` | Running average | Yes |
| `min` | Running minimum | Yes |
| `max` | Running maximum | Yes |
| `count` | Running count | No |
| `first` | First value in partition | Yes |
| `last` | Last value in partition | Yes |

### Examples

```yaml
# Row numbering
- op: window
  columns:
    - name: row_num
      func: row_number
      partition_by: [customer_id]
      order_by: [order_date]

# Previous value (lag)
- op: window
  columns:
    - name: prev_amount
      func: lag
      column: amount
      offset: 1
      partition_by: [customer_id]
      order_by: [order_date]
      default: 0

# Running total
- op: window
  columns:
    - name: running_total
      func: sum
      column: amount
      partition_by: [customer_id]
      order_by: [order_date]

# Multiple window columns
- op: window
  columns:
    - name: row_num
      func: row_number
      partition_by: [category]
      order_by: [sales desc]
    - name: pct_of_category
      func: sum
      column: sales
      partition_by: [category]
```

---

## pivot {#pivot}

Reshape data from long to wide format.

### Usage

```yaml
- op: pivot
  index: [region]
  columns: product
  values: revenue
  aggfunc: sum
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `index` | Yes | `list[str]` | Row identifier columns |
| `columns` | Yes | `str` | Column to pivot |
| `values` | Yes | `str` | Values to aggregate |
| `aggfunc` | No | `str` | Aggregation function (default: `first`) |

### Examples

```yaml
# Basic pivot
- op: pivot
  index: [region, quarter]
  columns: product
  values: revenue
  aggfunc: sum

# Result: Columns become region, quarter, product_A, product_B, ...
```

---

## unpivot {#unpivot}

Reshape data from wide to long format (melt).

### Usage

```yaml
- op: unpivot
  id_vars: [id, name]
  value_vars: [jan_sales, feb_sales, mar_sales]
  var_name: month
  value_name: sales
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `id_vars` | Yes | `list[str]` | Columns to keep as identifiers |
| `value_vars` | Yes | `list[str]` | Columns to unpivot |
| `var_name` | No | `str` | Name for variable column (default: `variable`) |
| `value_name` | No | `str` | Name for value column (default: `value`) |

### Examples

```yaml
# Unpivot monthly columns
- op: unpivot
  id_vars: [customer_id, name]
  value_vars: [jan, feb, mar, apr, may, jun]
  var_name: month
  value_name: sales

# Before: customer_id, name, jan, feb, mar, ...
# After:  customer_id, name, month, sales
```

---

## hash_key {#hash_key}

Generate a hash key from one or more columns.

### Usage

```yaml
- op: hash_key
  name: customer_hash
  columns: [customer_id, email]
  algorithm: md5
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `name` | Yes | `str` | Output column name |
| `columns` | Yes | `list[str]` | Columns to hash |
| `algorithm` | No | `str` | Hash algorithm: `md5`, `sha256`, `sha1` (default: `md5`) |
| `separator` | No | `str` | Separator between values (default: `\|`) |

### Examples

```yaml
# MD5 hash key
- op: hash_key
  name: row_hash
  columns: [id, name, email]
  algorithm: md5

# SHA-256 for security
- op: hash_key
  name: secure_hash
  columns: [ssn, dob]
  algorithm: sha256
  separator: "::"
```

---

## coalesce {#coalesce}

Return the first non-null value from a list of columns.

### Usage

```yaml
- op: coalesce
  name: email
  columns: [primary_email, secondary_email, fallback_email]
  default: "unknown@example.com"
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `name` | Yes | `str` | Output column name |
| `columns` | Yes | `list[str]` | Columns to check, in priority order |
| `default` | No | `any` | Default if all columns are null |

### Examples

```yaml
# Email fallback
- op: coalesce
  name: contact_email
  columns: [work_email, personal_email, alt_email]
  default: "no-email@example.com"

# Phone number priority
- op: coalesce
  name: phone
  columns: [mobile, home, work]
```

---

## chunk {#chunk}

Split text into smaller chunks for RAG pipelines.

!!! note "Requires Installation"
    `pip install "quicketl[chunking]"`

### Usage

```yaml
- op: chunk
  column: document_text
  strategy: recursive
  chunk_size: 512
  overlap: 50
  output_column: chunk_text
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `column` | Yes | `str` | Text column to chunk |
| `strategy` | No | `str` | `fixed`, `sentence`, `recursive` (default: `fixed`) |
| `chunk_size` | No | `int` | Maximum chunk size (default: 500) |
| `overlap` | No | `int` | Overlap between chunks (default: 0) |
| `output_column` | No | `str` | Output column name (default: `chunk_text`) |
| `add_chunk_index` | No | `bool` | Add chunk index column (default: false) |
| `count_tokens` | No | `bool` | Count tokens instead of chars (default: false) |
| `tokenizer` | No | `str` | Tokenizer name (default: `cl100k_base`) |
| `separators` | No | `list[str]` | Custom separators for recursive |

### Examples

```yaml
# Fixed-size chunks
- op: chunk
  column: content
  strategy: fixed
  chunk_size: 1000
  overlap: 100

# Recursive with custom separators
- op: chunk
  column: markdown_content
  strategy: recursive
  chunk_size: 512
  overlap: 50
  separators: ["\n## ", "\n\n", "\n", ". ", " "]
  add_chunk_index: true
```

See [AI Data Preparation](../ai-data-prep.md) for complete RAG pipeline examples.

---

## embed {#embed}

Generate vector embeddings from text.

!!! note "Requires Installation"
    `pip install "quicketl[embeddings-openai]"` or `pip install "quicketl[embeddings-huggingface]"`

### Usage

```yaml
- op: embed
  provider: openai
  model: text-embedding-3-small
  input_columns: [text]
  output_column: embedding
  api_key: ${secret:openai/api_key}
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `provider` | Yes | `str` | `openai` or `huggingface` |
| `model` | Yes | `str` | Model name |
| `input_columns` | Yes | `list[str]` | Columns to embed (concatenated) |
| `output_column` | No | `str` | Output column (default: `embedding`) |
| `batch_size` | No | `int` | Texts per API call (default: 100) |
| `api_key` | No | `str` | API key for OpenAI |
| `max_retries` | No | `int` | Retry attempts (default: 3) |

### Examples

```yaml
# OpenAI embeddings
- op: embed
  provider: openai
  model: text-embedding-3-small
  input_columns: [title, description]
  output_column: embedding
  batch_size: 100
  api_key: ${secret:openai/api_key}

# Local HuggingFace model
- op: embed
  provider: huggingface
  model: all-MiniLM-L6-v2
  input_columns: [chunk_text]
  output_column: embedding
```

See [AI Data Preparation](../ai-data-prep.md) for complete RAG pipeline examples.

---

## Related

- [Expression Language](../../reference/expressions.md) - Full expression syntax
- [Data Types](../../reference/data-types.md) - Type reference
- [Quality Checks](../quality/index.md) - Validate transformed data
- [AI Data Preparation](../ai-data-prep.md) - RAG pipeline guide
