# Troubleshooting Guide

Common issues and solutions when working with QuickETL.

## Installation Issues

### ModuleNotFoundError: No module named 'quicketl'

**Cause**: QuickETL not installed or wrong Python environment.

**Solution**:

```bash
# Install QuickETL
pip install quicketl

# Or with specific backend
pip install quicketl[duckdb]

# Verify installation
python -c "import quicketl; print(quicketl.__version__)"
```

### Backend Not Installed

```
ModuleNotFoundError: No module named 'duckdb'
```

**Solution**: Install the backend extra:

```bash
pip install quicketl[duckdb]
pip install quicketl[polars]
pip install quicketl[spark]
pip install quicketl[snowflake]
```

### Python Version Error

```
ERROR: Package 'quicketl' requires a different Python: 3.8.0 not in '>=3.10'
```

**Solution**: Upgrade Python to 3.10 or later:

```bash
# Check version
python --version

# Use pyenv to install newer version
pyenv install 3.12.0
pyenv local 3.12.0
```

## Configuration Errors

### Invalid YAML Syntax

```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Cause**: YAML indentation or syntax error.

**Solution**: Check YAML syntax:

```yaml
# Wrong: Inconsistent indentation
transforms:
- op: filter  # Missing space after -
  predicate: amount > 0

# Right: Consistent indentation
transforms:
  - op: filter
    predicate: amount > 0
```

Use a YAML validator or `quicketl validate`:

```bash
quicketl validate pipeline.yml
```

### Missing Required Field

```
Configuration is invalid
Errors:
  - sink: Field required
```

**Solution**: Add the required field:

```yaml
name: my_pipeline
source:
  type: file
  path: data.csv
  format: csv
sink:  # Add missing sink
  type: file
  path: output.parquet
  format: parquet
```

### Invalid Transform Operation

```
transforms -> 0 -> op: Input should be 'select', 'filter', 'rename', ...
```

**Cause**: Typo in transform operation name.

**Solution**: Use correct operation name:

```yaml
# Wrong
transforms:
  - op: filtter  # Typo!

# Right
transforms:
  - op: filter
```

Valid operations: `select`, `rename`, `filter`, `derive_column`, `cast`, `fill_null`, `dedup`, `sort`, `join`, `aggregate`, `union`, `limit`

### Variable Not Found

```
KeyError: 'DATE'
```

**Cause**: Variable referenced but not provided.

**Solution**: Provide the variable:

```bash
quicketl run pipeline.yml --var DATE=2025-01-15
```

Or use defaults:

```yaml
path: data/sales_${DATE:-2025-01-01}.csv
```

## Runtime Errors

### File Not Found

```
FileNotFoundError: data/input.csv not found
```

**Solution**: Verify path:

```bash
# Check file exists
ls -la data/input.csv

# Check current directory
pwd

# Use absolute path
quicketl run pipeline.yml --var INPUT_PATH=/absolute/path/to/data.csv
```

### Permission Denied

```
PermissionError: [Errno 13] Permission denied: 'output/results.parquet'
```

**Solution**: Check permissions:

```bash
# Check directory permissions
ls -la output/

# Create directory with proper permissions
mkdir -p output
chmod 755 output
```

### Out of Memory

```
MemoryError: Unable to allocate array
```

**Solutions**:

1. Use a more memory-efficient backend:

```bash
quicketl run pipeline.yml --engine polars  # Streaming support
```

2. Filter data early:

```yaml
transforms:
  - op: filter
    predicate: date >= '2025-01-01'  # Reduce data first
```

3. Select only needed columns:

```yaml
transforms:
  - op: select
    columns: [id, amount, date]
```

### Database Connection Failed

```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solutions**:

1. Verify database is running:

```bash
pg_isready -h localhost -p 5432
```

2. Check credentials:

```bash
psql -h localhost -U user -d database
```

3. Verify environment variables:

```bash
echo $POSTGRES_HOST
echo $POSTGRES_PORT
```

4. Check firewall/network:

```bash
telnet db.example.com 5432
```

## Quality Check Failures

### Not Null Check Failed

```
Quality Checks: FAILED
  ✗ not_null: email (42 NULL values found)
```

**Solutions**:

1. Fix data quality at source
2. Fill NULL values:

```yaml
transforms:
  - op: fill_null
    columns:
      email: "unknown@example.com"
```

3. Filter out NULLs:

```yaml
transforms:
  - op: filter
    predicate: email IS NOT NULL
```

### Unique Check Failed

```
✗ unique: id (152 duplicates found)
```

**Solutions**:

1. Deduplicate:

```yaml
transforms:
  - op: dedup
    columns: [id]
    keep: first
```

2. Investigate source data for duplicates

### Row Count Check Failed

```
✗ row_count: min=1 (0 rows found)
```

**Cause**: Empty result after transforms.

**Solutions**:

1. Check filter conditions aren't too restrictive
2. Verify source data isn't empty
3. Check join conditions

## Backend-Specific Issues

### DuckDB

**Large CSV parsing slow:**

```bash
# Convert to Parquet first
duckdb -c "COPY (SELECT * FROM 'large.csv') TO 'large.parquet'"
```

### Spark

**Java not found:**

```
JAVA_HOME is not set
```

**Solution**:

```bash
# macOS
brew install openjdk@17
export JAVA_HOME=/opt/homebrew/opt/openjdk@17

# Ubuntu
sudo apt install openjdk-17-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

### Snowflake

**Account not found:**

```
Account 'xyz' not found
```

**Solution**: Use full account identifier:

```bash
export SNOWFLAKE_ACCOUNT=xy12345.us-east-1
# Not just: SNOWFLAKE_ACCOUNT=xy12345
```

### BigQuery

**Quota exceeded:**

```
Quota exceeded: Your project exceeded quota for concurrent queries
```

**Solution**: Wait and retry, or request quota increase in GCP Console.

## Performance Issues

### Pipeline Running Slowly

**Diagnosis**:

```bash
quicketl run pipeline.yml --verbose
```

Look for slow steps.

**Common causes and solutions**:

1. **Reading CSV**: Use Parquet instead

2. **Late filtering**: Move filters earlier

3. **Large joins**: Filter before joining

4. **Wrong backend**: Try DuckDB or Polars for local files

### High Memory Usage

**Solutions**:

1. Use Polars (streaming support):

```bash
quicketl run pipeline.yml --engine polars
```

2. Select fewer columns

3. Process in date partitions:

```bash
for date in 2025-01-{01..31}; do
  quicketl run pipeline.yml --var DATE=$date
done
```

## Getting Help

### Check Version

```bash
quicketl --version
quicketl info --backends --check
```

### Verbose Output

```bash
quicketl run pipeline.yml --verbose
```

### Validate Configuration

```bash
quicketl validate pipeline.yml --verbose
```

### Report Issues

If you've found a bug:

1. Check existing issues: https://github.com/your-org/quicketl/issues
2. Create minimal reproduction
3. Include:
   - QuickETL version
   - Python version
   - Operating system
   - Complete error message
   - Minimal pipeline YAML

## Related

- [Error Handling](../best-practices/error-handling.md) - Error handling strategies
- [Performance](../best-practices/performance.md) - Optimization tips
- [Backend Selection](../user-guide/backends/index.md) - Choose the right backend
