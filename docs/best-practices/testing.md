# Testing Best Practices

Strategies for testing QuickETL pipelines to ensure data quality and reliability.

## Testing Pyramid

```
         /\
        /  \
       / E2E \        Integration tests (full pipeline)
      /--------\
     /   Unit   \     Component tests (transforms, checks)
    /--------------\
   /   Validation   \  Schema & config validation
  /------------------\
```

## Configuration Validation

### Validate Before Running

```bash
# Always validate first
quicketl validate pipeline.yml

# Validate all pipelines
for f in pipelines/*.yml; do
  quicketl validate "$f" || exit 1
done
```

### CI/CD Validation

```yaml
# .github/workflows/validate.yml
name: Validate Pipelines

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install QuickETL
        run: pip install quicketl[duckdb]

      - name: Validate all pipelines
        run: |
          for f in pipelines/*.yml; do
            echo "Validating $f..."
            quicketl validate "$f"
          done
```

## Sample Data Testing

### Create Test Fixtures

Create representative test data:

```
tests/
├── fixtures/
│   ├── orders_valid.csv
│   ├── orders_with_nulls.csv
│   ├── orders_empty.csv
│   └── orders_duplicates.csv
└── pipelines/
    └── test_pipeline.yml
```

### Test Fixture: Valid Data

`tests/fixtures/orders_valid.csv`:

```csv
id,customer_id,amount,status,date
1,C001,99.99,completed,2025-01-15
2,C002,149.99,completed,2025-01-15
3,C003,49.99,completed,2025-01-16
```

### Test Fixture: Edge Cases

`tests/fixtures/orders_with_nulls.csv`:

```csv
id,customer_id,amount,status,date
1,C001,99.99,completed,2025-01-15
2,,149.99,completed,2025-01-15
3,C003,,pending,2025-01-16
4,C004,49.99,,2025-01-16
```

### Test Pipeline

`tests/pipelines/test_pipeline.yml`:

```yaml
name: test_pipeline
engine: duckdb

source:
  type: file
  path: ${TEST_DATA_PATH}
  format: csv

transforms:
  - op: filter
    predicate: status = 'completed'
  - op: derive_column
    name: amount_with_tax
    expr: amount * 1.1

checks:
  - check: not_null
    columns: [id, customer_id, amount]
  - check: unique
    columns: [id]

sink:
  type: file
  path: ${OUTPUT_PATH}
  format: parquet
```

## Unit Tests with pytest

### Test Setup

```python
# tests/conftest.py
import pytest
import tempfile
import os
from pathlib import Path

@pytest.fixture
def test_data_dir():
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_orders(test_data_dir):
    return test_data_dir / "orders_valid.csv"
```

### Test Pipeline Execution

```python
# tests/test_pipelines.py
import pytest
from quicketl import Pipeline

def test_basic_pipeline_runs(sample_orders, temp_output_dir):
    """Test that pipeline executes successfully."""
    pipeline = Pipeline.from_yaml("pipelines/orders.yml")

    result = pipeline.run(variables={
        "INPUT_PATH": str(sample_orders),
        "OUTPUT_PATH": str(temp_output_dir / "output.parquet")
    })

    assert result.status == "SUCCESS"
    assert result.rows_written > 0

def test_pipeline_filters_correctly(sample_orders, temp_output_dir):
    """Test that filter transform works correctly."""
    pipeline = Pipeline.from_yaml("pipelines/orders.yml")

    result = pipeline.run(variables={
        "INPUT_PATH": str(sample_orders),
        "OUTPUT_PATH": str(temp_output_dir / "output.parquet")
    })

    # Read output and verify filter worked
    import pandas as pd
    output = pd.read_parquet(temp_output_dir / "output.parquet")

    assert all(output["status"] == "completed")

def test_quality_checks_pass(sample_orders, temp_output_dir):
    """Test that quality checks pass for valid data."""
    pipeline = Pipeline.from_yaml("pipelines/orders.yml")

    result = pipeline.run(variables={
        "INPUT_PATH": str(sample_orders),
        "OUTPUT_PATH": str(temp_output_dir / "output.parquet")
    })

    assert result.checks_failed == 0
    assert result.checks_passed > 0
```

### Test Edge Cases

```python
# tests/test_edge_cases.py
import pytest
from quicketl import Pipeline
from quicketl.exceptions import QualityCheckError

def test_empty_input_file(test_data_dir, temp_output_dir):
    """Test handling of empty input file."""
    pipeline = Pipeline.from_yaml("pipelines/orders.yml")

    result = pipeline.run(
        variables={
            "INPUT_PATH": str(test_data_dir / "orders_empty.csv"),
            "OUTPUT_PATH": str(temp_output_dir / "output.parquet")
        },
        fail_on_checks=False
    )

    # row_count check should fail for empty file
    assert result.checks_failed > 0

def test_null_handling(test_data_dir, temp_output_dir):
    """Test that NULL values are handled correctly."""
    pipeline = Pipeline.from_yaml("pipelines/orders.yml")

    with pytest.raises(QualityCheckError):
        pipeline.run(
            variables={
                "INPUT_PATH": str(test_data_dir / "orders_with_nulls.csv"),
                "OUTPUT_PATH": str(temp_output_dir / "output.parquet")
            },
            fail_on_checks=True
        )

def test_duplicate_handling(test_data_dir, temp_output_dir):
    """Test deduplication logic."""
    pipeline = Pipeline.from_yaml("pipelines/dedup_orders.yml")

    result = pipeline.run(variables={
        "INPUT_PATH": str(test_data_dir / "orders_duplicates.csv"),
        "OUTPUT_PATH": str(temp_output_dir / "output.parquet")
    })

    import pandas as pd
    output = pd.read_parquet(temp_output_dir / "output.parquet")

    # Verify no duplicates in output
    assert output["id"].is_unique
```

## Integration Tests

### Full Pipeline Test

```python
# tests/test_integration.py
import pytest
from quicketl import Pipeline

@pytest.mark.integration
def test_full_etl_pipeline(test_data_dir, temp_output_dir):
    """Test complete ETL workflow."""
    # Step 1: Extract
    extract = Pipeline.from_yaml("pipelines/extract.yml")
    extract_result = extract.run(variables={
        "INPUT_PATH": str(test_data_dir / "source_data"),
        "OUTPUT_PATH": str(temp_output_dir / "staging")
    })
    assert extract_result.status == "SUCCESS"

    # Step 2: Transform
    transform = Pipeline.from_yaml("pipelines/transform.yml")
    transform_result = transform.run(variables={
        "INPUT_PATH": str(temp_output_dir / "staging"),
        "OUTPUT_PATH": str(temp_output_dir / "processed")
    })
    assert transform_result.status == "SUCCESS"

    # Step 3: Validate output
    import pandas as pd
    output = pd.read_parquet(temp_output_dir / "processed" / "data.parquet")

    # Assertions on final output
    assert len(output) > 0
    assert "calculated_field" in output.columns
    assert output["calculated_field"].notna().all()
```

## Schema Testing

### Verify Output Schema

```python
def test_output_schema(sample_orders, temp_output_dir):
    """Verify output has expected columns and types."""
    pipeline = Pipeline.from_yaml("pipelines/orders.yml")

    result = pipeline.run(variables={
        "INPUT_PATH": str(sample_orders),
        "OUTPUT_PATH": str(temp_output_dir / "output.parquet")
    })

    import pandas as pd
    output = pd.read_parquet(temp_output_dir / "output.parquet")

    # Check expected columns exist
    expected_columns = ["id", "customer_id", "amount", "amount_with_tax"]
    assert all(col in output.columns for col in expected_columns)

    # Check data types
    assert output["id"].dtype == "int64"
    assert output["amount"].dtype == "float64"
```

## Test Automation

### pytest Configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
markers =
    integration: marks tests as integration tests
    slow: marks tests as slow
```

### Run Tests

```bash
# Run all tests
pytest

# Run only unit tests (exclude integration)
pytest -m "not integration"

# Run with coverage
pytest --cov=quicketl --cov-report=html

# Run verbose
pytest -v
```

## Pre-commit Hooks

### Setup

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-pipelines
        name: Validate QuickETL Pipelines
        entry: bash -c 'for f in pipelines/*.yml; do quicketl validate "$f" || exit 1; done'
        language: system
        files: \.yml$
        pass_filenames: false
```

### Install

```bash
pip install pre-commit
pre-commit install
```

## Test Data Generation

### Generate Realistic Test Data

```python
# scripts/generate_test_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_orders(n=1000):
    np.random.seed(42)

    return pd.DataFrame({
        "id": range(1, n + 1),
        "customer_id": [f"C{i:04d}" for i in np.random.randint(1, 100, n)],
        "amount": np.random.uniform(10, 500, n).round(2),
        "status": np.random.choice(
            ["completed", "pending", "cancelled"],
            n,
            p=[0.8, 0.15, 0.05]
        ),
        "date": [
            (datetime(2025, 1, 1) + timedelta(days=int(d))).strftime("%Y-%m-%d")
            for d in np.random.randint(0, 30, n)
        ]
    })

if __name__ == "__main__":
    orders = generate_orders(1000)
    orders.to_csv("tests/fixtures/orders_generated.csv", index=False)
```

## Related

- [Error Handling](error-handling.md) - Handle test failures
- [CI/CD Integration](../integrations/index.md) - Automated testing
- [Quality Checks](../user-guide/quality/index.md) - Data validation
