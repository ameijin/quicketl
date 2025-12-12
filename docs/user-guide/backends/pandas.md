# Pandas Backend

Pandas is the most widely-used Python data analysis library. ETLX supports Pandas via Ibis for compatibility with existing workflows.

## Installation

Pandas is included with the base ETLX installation:

```bash
pip install quicketl
# or
uv add quicketl
```

## When to Use Pandas

**Ideal for:**

- Compatibility with existing Pandas code
- Datasets that fit in memory
- When you need extensive Pandas ecosystem
- Quick prototyping

**Consider alternatives when:**

- Performance is critical (use DuckDB or Polars)
- Large datasets (use Spark or chunked processing)
- Production workloads (use DuckDB)

## Configuration

### Basic Usage

```yaml
name: pandas_pipeline
engine: pandas

source:
  type: file
  path: data/sales.csv
  format: csv

transforms:
  - op: filter
    predicate: amount > 0
  - op: aggregate
    group_by: [category]
    aggregations:
      total: sum(amount)

sink:
  type: file
  path: output/summary.csv
  format: csv
```

### CLI Override

```bash
quicketl run pipeline.yml --engine pandas
```

## Performance Characteristics

| Metric | Performance |
|--------|-------------|
| Startup time | ~200ms |
| Memory efficiency | Moderate |
| Parallelism | Single-threaded* |
| Ecosystem | Extensive |

*Some operations use NumPy's parallel operations.

## Supported Features

### Transforms

| Transform | Support | Notes |
|-----------|---------|-------|
| select | Full | |
| rename | Full | |
| filter | Full | |
| derive_column | Full | |
| cast | Full | |
| fill_null | Full | |
| dedup | Full | |
| sort | Full | |
| join | Full | |
| aggregate | Full | |
| union | Full | |
| limit | Full | |

### Data Types

| ETLX Type | Pandas Type |
|-----------|-------------|
| string | object / string |
| int | int64 |
| float | float64 |
| bool | bool |
| date | datetime64[ns] |
| timestamp | datetime64[ns] |
| decimal | float64 |

## File Format Support

### CSV

```yaml
source:
  type: file
  path: data/input.csv
  format: csv
  options:
    encoding: utf-8
    delimiter: ","
```

### Excel

```yaml
source:
  type: file
  path: data/report.xlsx
  format: excel
  options:
    sheet_name: Sheet1
```

### Parquet

```yaml
source:
  type: file
  path: data/input.parquet
  format: parquet
```

### JSON

```yaml
source:
  type: file
  path: data/records.json
  format: json
  options:
    orient: records
```

## Memory Optimization

### 1. Use Appropriate Data Types

Pandas can use significant memory. Optimize with type casting:

```yaml
transforms:
  - op: cast
    columns:
      id: int32  # Instead of int64
      amount: float32  # Instead of float64
      category: category  # Pandas categorical
```

### 2. Select Only Needed Columns

```yaml
transforms:
  - op: select
    columns: [id, name, amount]
```

### 3. Filter Early

```yaml
transforms:
  - op: filter
    predicate: date >= '2025-01-01'

  # Then do memory-intensive operations
  - op: aggregate
    group_by: [category]
    aggregations:
      total: sum(amount)
```

## Example: Data Analysis Pipeline

```yaml
name: sales_analysis
description: Analyze sales data with Pandas
engine: pandas

source:
  type: file
  path: data/sales.csv
  format: csv

transforms:
  # Clean data
  - op: filter
    predicate: amount > 0

  # Fill missing values
  - op: fill_null
    columns:
      category: Unknown
      discount: 0

  # Calculate derived metrics
  - op: derive_column
    name: net_amount
    expr: amount - discount

  - op: derive_column
    name: profit_margin
    expr: (amount - cost) / amount

  # Aggregate by category
  - op: aggregate
    group_by: [category]
    aggregations:
      total_sales: sum(net_amount)
      avg_margin: avg(profit_margin)
      order_count: count(*)

  # Sort by total sales
  - op: sort
    by:
      - column: total_sales
        order: desc

checks:
  - check: not_null
    columns: [category, total_sales]
  - check: expression
    expr: total_sales >= 0

sink:
  type: file
  path: output/category_analysis.csv
  format: csv
```

## Chunked Processing

For files larger than memory, Pandas can read in chunks. However, this is handled automatically by ETLX when possible. For very large files, consider using DuckDB or Polars instead.

## Pandas-Specific Features

While ETLX provides a backend-agnostic API, you can leverage Pandas features:

### DateTime Operations

```yaml
transforms:
  - op: derive_column
    name: month
    expr: extract(month from order_date)

  - op: derive_column
    name: day_of_week
    expr: extract(dow from order_date)
```

### String Operations

```yaml
transforms:
  - op: derive_column
    name: name_upper
    expr: upper(name)

  - op: derive_column
    name: email_domain
    expr: split_part(email, '@', 2)
```

## Comparison with Other Backends

| Feature | Pandas | DuckDB | Polars |
|---------|--------|--------|--------|
| Ecosystem | Extensive | Growing | Growing |
| Performance | Moderate | Fast | Fast |
| Memory usage | High | Low | Low |
| Learning curve | Low | Low | Medium |
| Production ready | Yes* | Yes | Yes |

*With appropriate memory management.

## Limitations

1. **Memory Usage**: Loads entire dataset into memory
2. **Performance**: Single-threaded for most operations
3. **Large Files**: Not suitable for files > available RAM
4. **Production**: Consider DuckDB/Polars for better performance

## When to Migrate to Other Backends

Consider switching from Pandas when:

- Processing takes too long
- Memory errors occur
- Dataset size exceeds 1GB
- Running in production

Migration is easy - just change the engine:

```yaml
# Before
engine: pandas

# After
engine: duckdb  # or polars
```

## Troubleshooting

### Memory Error

```
MemoryError: Unable to allocate array
```

**Solutions**:
1. Use DuckDB or Polars instead
2. Read fewer columns
3. Filter data at source
4. Use chunked processing

### Slow Performance

If pipeline is slow:

1. Profile with `--verbose`
2. Consider switching to DuckDB or Polars
3. Optimize data types
4. Filter early

### Type Inference Issues

```
DtypeWarning: Columns have mixed types
```

**Solution**: Specify types explicitly:
```yaml
source:
  type: file
  path: data.csv
  format: csv
  options:
    dtype:
      id: int64
      amount: float64
```

## Related

- [Backend Selection](index.md) - Choosing the right backend
- [DuckDB](duckdb.md) - Faster alternative
- [Polars](polars.md) - Modern DataFrame library
