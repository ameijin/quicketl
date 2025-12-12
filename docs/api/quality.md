# Quality Check Classes

ETLX provides data quality check classes for programmatic validation. These classes can be used directly or via configuration models.

## Import

```python
from etlx.quality import (
    NotNullCheck,
    UniqueCheck,
    RowCountCheck,
    AcceptedValuesCheck,
    ExpressionCheck,
    CheckRunner,
    CheckResult,
    CheckResults
)
```

## Check Classes

### NotNullCheck

Validates that specified columns contain no NULL values.

```python
class NotNullCheck:
    def __init__(self, columns: list[str])
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `columns` | `list[str]` | Columns to check for NULLs |

**Example:**

```python
from etlx.quality import NotNullCheck

check = NotNullCheck(columns=["id", "email", "created_at"])
```

---

### UniqueCheck

Validates that values in specified columns are unique.

```python
class UniqueCheck:
    def __init__(self, columns: list[str])
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `columns` | `list[str]` | Columns that should be unique (individually or combined) |

**Example:**

```python
from etlx.quality import UniqueCheck

# Single column uniqueness
check = UniqueCheck(columns=["id"])

# Composite uniqueness
check = UniqueCheck(columns=["order_id", "product_id"])
```

---

### RowCountCheck

Validates the number of rows in the result.

```python
class RowCountCheck:
    def __init__(
        self,
        min: int | None = None,
        max: int | None = None,
        exact: int | None = None
    )
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `min` | `int \| None` | Minimum row count |
| `max` | `int \| None` | Maximum row count |
| `exact` | `int \| None` | Exact row count (overrides min/max) |

**Example:**

```python
from etlx.quality import RowCountCheck

# At least 1 row
check = RowCountCheck(min=1)

# Between 100 and 10000 rows
check = RowCountCheck(min=100, max=10000)

# Exactly 1000 rows
check = RowCountCheck(exact=1000)
```

---

### AcceptedValuesCheck

Validates that a column contains only allowed values.

```python
class AcceptedValuesCheck:
    def __init__(
        self,
        column: str,
        values: list[Any]
    )
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `column` | `str` | Column to validate |
| `values` | `list[Any]` | List of accepted values |

**Example:**

```python
from etlx.quality import AcceptedValuesCheck

# Validate status values
check = AcceptedValuesCheck(
    column="status",
    values=["pending", "active", "completed", "cancelled"]
)

# Validate boolean-like values
check = AcceptedValuesCheck(
    column="is_active",
    values=[0, 1, True, False]
)
```

---

### ExpressionCheck

Validates rows using a custom SQL expression.

```python
class ExpressionCheck:
    def __init__(
        self,
        expr: str,
        threshold: float = 1.0
    )
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `expr` | `str` | Boolean SQL expression |
| `threshold` | `float` | Fraction of rows that must pass (0.0 to 1.0) |

**Example:**

```python
from etlx.quality import ExpressionCheck

# All rows must pass
check = ExpressionCheck(expr="amount > 0")

# At least 95% must pass
check = ExpressionCheck(
    expr="email LIKE '%@%.%'",
    threshold=0.95
)

# Complex expression
check = ExpressionCheck(
    expr="start_date <= end_date AND status IN ('active', 'pending')"
)
```

## CheckRunner

Execute checks against a table.

```python
class CheckRunner:
    def __init__(self, engine: ETLXEngine)

    def run(
        self,
        table: Table,
        checks: list[Check]
    ) -> CheckResults
```

**Example:**

```python
from etlx import ETLXEngine
from etlx.quality import (
    CheckRunner,
    NotNullCheck,
    UniqueCheck,
    RowCountCheck
)

# Setup
engine = ETLXEngine(backend="duckdb")
runner = CheckRunner(engine)

# Read data
table = engine.read_source({
    "type": "file",
    "path": "data/users.parquet",
    "format": "parquet"
})

# Define checks
checks = [
    NotNullCheck(columns=["id", "email"]),
    UniqueCheck(columns=["id"]),
    UniqueCheck(columns=["email"]),
    RowCountCheck(min=1)
]

# Run checks
results = runner.run(table, checks)

print(f"Passed: {results.passed}/{results.total}")
for detail in results.details:
    status = "✓" if detail.passed else "✗"
    print(f"  {status} {detail.name}: {detail.message}")
```

## Result Classes

### CheckResult

Individual check result.

```python
class CheckResult:
    name: str           # Check name/description
    passed: bool        # Whether check passed
    message: str        # Human-readable result
    details: dict       # Additional details
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Check name (e.g., "not_null: id, email") |
| `passed` | `bool` | Whether the check passed |
| `message` | `str` | Result message |
| `details` | `dict` | Additional metadata |

---

### CheckResults

Collection of check results.

```python
class CheckResults:
    passed: int              # Number of passed checks
    failed: int              # Number of failed checks
    total: int               # Total checks
    details: list[CheckResult]  # Individual results
```

**Methods:**

```python
# Check if all passed
if results.all_passed:
    print("All checks passed!")

# Iterate failed checks
for result in results.failed_checks:
    print(f"Failed: {result.name} - {result.message}")

# Convert to dict/JSON
data = results.to_dict()
json_str = results.to_json()
```

## Custom Check Classes

Create custom checks by extending the base class:

```python
from etlx.quality import BaseCheck, CheckResult

class CustomRangeCheck(BaseCheck):
    """Check that numeric values are within a range."""

    def __init__(self, column: str, min_val: float, max_val: float):
        self.column = column
        self.min_val = min_val
        self.max_val = max_val

    @property
    def name(self) -> str:
        return f"range_check: {self.column} [{self.min_val}, {self.max_val}]"

    def run(self, table, engine) -> CheckResult:
        # Count rows outside range
        expr = f"{self.column} < {self.min_val} OR {self.column} > {self.max_val}"
        invalid_count = table.filter(expr).count().execute()
        total_count = table.count().execute()

        passed = invalid_count == 0
        message = (
            f"All values in range" if passed
            else f"{invalid_count}/{total_count} values out of range"
        )

        return CheckResult(
            name=self.name,
            passed=passed,
            message=message,
            details={
                "invalid_count": invalid_count,
                "total_count": total_count
            }
        )

# Usage
check = CustomRangeCheck(column="age", min_val=0, max_val=150)
```

## Complete Example

```python
from etlx import ETLXEngine
from etlx.quality import (
    CheckRunner,
    NotNullCheck,
    UniqueCheck,
    RowCountCheck,
    AcceptedValuesCheck,
    ExpressionCheck
)

# Initialize
engine = ETLXEngine(backend="duckdb")
runner = CheckRunner(engine)

# Load data
table = engine.read_source({
    "type": "file",
    "path": "data/orders.parquet",
    "format": "parquet"
})

# Apply transforms
table = engine.apply_transforms(table, [
    {"op": "filter", "predicate": "status != 'cancelled'"}
])

# Define comprehensive checks
checks = [
    # Required fields
    NotNullCheck(columns=["order_id", "customer_id", "amount"]),

    # Primary key
    UniqueCheck(columns=["order_id"]),

    # Data presence
    RowCountCheck(min=1, max=1000000),

    # Valid status values
    AcceptedValuesCheck(
        column="status",
        values=["pending", "processing", "shipped", "delivered"]
    ),

    # Business rules
    ExpressionCheck(expr="amount > 0"),
    ExpressionCheck(expr="quantity >= 1"),
    ExpressionCheck(expr="order_date <= ship_date OR ship_date IS NULL"),

    # Data quality threshold (95% must have valid email)
    ExpressionCheck(
        expr="email LIKE '%@%.%'",
        threshold=0.95
    )
]

# Run all checks
results = runner.run(table, checks)

# Report results
print(f"\nQuality Check Results: {results.passed}/{results.total} passed\n")

for result in results.details:
    icon = "✓" if result.passed else "✗"
    print(f"  {icon} {result.name}")
    if not result.passed:
        print(f"    → {result.message}")

# Fail pipeline if checks failed
if not results.all_passed:
    raise Exception(f"Quality checks failed: {results.failed} failures")
```

## Related

- [Quality Checks Guide](../user-guide/quality/index.md) - YAML configuration
- [Pipeline API](pipeline.md) - Running checks in pipelines
- [Best Practices](../best-practices/testing.md) - Testing strategies
