# Example: Local CSV to Parquet

Reads a CSV file, filters and transforms the data, and writes to Parquet.

## Run

```bash
cd examples/01-local-csv
quicketl run pipeline.yml
```

Or with Python:

```python
from quicketl import Pipeline

result = Pipeline.from_yaml("examples/01-local-csv/pipeline.yml").run()
print(result.summary())
```
