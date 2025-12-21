# Contributing to QuickETL

Thank you for your interest in contributing to QuickETL! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Test-Driven Development](#test-driven-development)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Style Guide](#style-guide)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a branch for your changes
5. Make your changes and test them
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.12 or later
- uv (recommended) or pip

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/quicketl.git
cd quicketl

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install in development mode with all extras
uv pip install -e ".[dev,docs]"

# Install pre-commit hooks (if available)
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=quicketl --cov-report=html

# Run specific test file
pytest tests/test_transforms.py

# Run tests matching a pattern
pytest -k "test_filter"
```

### Running Linters

```bash
# Run ruff linter
ruff check src/ tests/

# Run ruff formatter
ruff format src/ tests/

# Run type checker
mypy src/
```

## Making Changes

### Branch Naming

Use descriptive branch names:

- `feature/add-window-functions` - New features
- `fix/filter-null-handling` - Bug fixes
- `docs/improve-transform-examples` - Documentation
- `refactor/simplify-engine-init` - Code refactoring

### Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for **automated semantic versioning**. Your commit messages determine how versions are bumped automatically when merged to `main`.

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types and Version Bumps:**

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | **Minor** (0.x.0) |
| `fix` | Bug fix | **Patch** (0.0.x) |
| `perf` | Performance improvement | **Patch** (0.0.x) |
| `refactor` | Code refactoring | No bump |
| `docs` | Documentation changes | No bump |
| `style` | Code style changes (formatting, etc.) | No bump |
| `test` | Adding or updating tests | No bump |
| `build` | Build system changes | No bump |
| `ci` | CI/CD changes | No bump |
| `chore` | Maintenance tasks | No bump |

**Breaking Changes (Major bump):**

For breaking changes that require a **Major** version bump (x.0.0), add `BREAKING CHANGE:` in the commit body or append `!` after the type:

```
feat!: remove deprecated API endpoint

BREAKING CHANGE: The /v1/old endpoint has been removed. Use /v2/new instead.
```

**Examples:**

```
feat(pipeline): add support for incremental loads

Adds delta detection for efficient incremental data processing.
```

```
fix(cli): correct exit code on validation errors
```

```
docs(api): add examples for Pipeline builder pattern
```

## Test-Driven Development

QuickETL follows Test-Driven Development (TDD) practices. This ensures code quality, prevents regressions, and makes the codebase maintainable.

### The TDD Workflow (Red-Green-Refactor)

When fixing bugs, always follow this workflow:

1. **RED**: Write a failing test that reproduces the bug
   ```bash
   # Write the test first
   pytest tests/unit/engines/test_parse_predicate.py::test_predicate_with_null_comparison -v
   # Confirm it fails (reproduces the bug)
   ```

2. **GREEN**: Fix the code to make the test pass
   ```bash
   # Make the minimal change to fix the bug
   pytest tests/unit/engines/test_parse_predicate.py::test_predicate_with_null_comparison -v
   # Confirm it passes
   ```

3. **REFACTOR**: Clean up without changing behavior
   ```bash
   # Run all related tests to ensure no regressions
   pytest tests/unit/engines/ -v
   ```

### Test Naming Convention

Use descriptive names that explain what is being tested:

```
test_<what>_<condition>_<expected_result>
```

**Examples:**
- `test_filter_with_null_values_excludes_nulls`
- `test_parse_predicate_with_invalid_syntax_raises_value_error`
- `test_cli_run_with_dry_run_flag_writes_no_output`
- `test_variable_substitution_with_default_uses_fallback`

### Test Types

| Type | Location | Purpose | Speed |
|------|----------|---------|-------|
| **Unit** | `tests/unit/` | Isolated component tests, no external deps | Fast (<100ms) |
| **Integration** | `tests/integration/` | Real databases, full pipelines | Slow (seconds) |
| **Parity** | `tests/parity/` | Verify behavior consistency across backends | Medium |
| **Hypothesis** | Mixed | Property-based fuzzing for edge cases | Varies |

**When to use each:**

- **Unit tests**: Default choice. Test individual functions/methods in isolation. Mock external dependencies.
- **Integration tests**: When testing database connections, file I/O with real files, or end-to-end workflows.
- **Parity tests**: When adding/modifying transforms to ensure duckdb and polars produce identical results.
- **Hypothesis tests**: For parsers, validators, and any code with complex input handling. Finds edge cases you wouldn't think of.

### Running Tests

```bash
# Run all tests
pytest

# Run only unit tests (fast)
pytest tests/unit/

# Run excluding integration tests
pytest -m "not integration"

# Run with coverage report
pytest --cov=quicketl --cov-report=html

# Run specific test file
pytest tests/unit/engines/test_parse_predicate.py

# Run tests matching a pattern
pytest -k "test_filter"

# Run with verbose output
pytest -v

# Run hypothesis tests only
pytest -m hypothesis
```

### Test Markers

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.slow
def test_large_dataset_processing():
    """Tests that take > 5 seconds."""
    ...

@pytest.mark.integration
def test_postgres_connection():
    """Tests requiring external services."""
    ...

@pytest.mark.parity
def test_filter_same_across_backends():
    """Tests verifying backend consistency."""
    ...

@pytest.mark.hypothesis
def test_predicate_parsing_with_random_input():
    """Property-based tests."""
    ...
```

### Property-Based Testing with Hypothesis

Use hypothesis for testing parsers and validators:

```python
from hypothesis import given, strategies as st
import string

@pytest.mark.hypothesis
@given(st.integers(min_value=-1000000, max_value=1000000))
def test_numeric_literal_parsing(value):
    """Any integer should parse correctly in predicates."""
    engine = ETLXEngine(backend="duckdb")
    # Create table and test predicate parsing
    ...

@pytest.mark.hypothesis
@given(st.text(alphabet=string.ascii_letters + "_", min_size=1, max_size=50))
def test_column_name_parsing(col_name):
    """Valid identifiers should work as column names."""
    ...

@pytest.mark.hypothesis
@given(st.text().filter(lambda s: "${" not in s))
def test_string_without_vars_unchanged(text):
    """Strings without ${} should pass through unchanged."""
    result = substitute_variables(text, {})
    assert result == text
```

## Testing

### Test Requirements

- All new features must have tests
- All bug fixes must have regression tests (following TDD workflow)
- Maintain >75% overall code coverage
  - Core modules (engines, pipeline, config, quality): aim for >80%
  - Integration modules (generators, airflow): coverage may be lower
- Tests must pass on all supported Python versions (3.12, 3.13)

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── fixtures/                # Test data files
├── unit/                    # Fast, isolated tests
│   ├── cli/                 # CLI command tests
│   ├── config/              # Config parsing tests
│   ├── engines/             # Transform & parser tests
│   ├── io/                  # Reader/writer tests
│   ├── pipeline/            # Pipeline execution tests
│   ├── quality/             # Check implementation tests
│   └── workflow/            # Workflow orchestration tests
├── integration/             # Tests with external dependencies
│   └── conftest.py          # Docker/DB fixtures
└── parity/                  # Backend parity tests
    └── conftest.py          # Multi-backend fixtures
```

### Writing Tests

```python
import pytest
from quicketl import Pipeline
from quicketl.config.transforms import FilterTransform


class TestFilterTransform:
    """Tests for the filter transform operation."""

    def test_filter_basic(self, sample_engine):
        """Test basic filter with simple predicate."""
        # Arrange
        table = sample_engine.read_file("tests/fixtures/sales.csv", "csv")

        # Act
        result = sample_engine.filter(table, "amount > 100")

        # Assert
        assert sample_engine.row_count(result) == 5

    @pytest.mark.parametrize("engine", ["duckdb", "polars"])
    def test_filter_backend_parity(self, engine):
        """Verify filter produces same results across backends."""
        # Test that different backends produce identical results
        pass
```

## Documentation

### Building Docs Locally

```bash
# Install docs dependencies
uv pip install -e ".[docs]"

# Serve docs locally with hot reload
mkdocs serve

# Build static site
mkdocs build

# Check for errors
mkdocs build --strict
```

### Documentation Guidelines

- Use clear, concise language
- Include code examples for all features
- Add type hints to all function signatures
- Write docstrings in Google style
- Cross-reference related documentation

### Docstring Format

```python
def aggregate(
    self,
    table: ir.Table,
    group_by: list[str],
    aggs: dict[str, str],
) -> ir.Table:
    """Group and aggregate data.

    Args:
        table: Input Ibis table expression.
        group_by: Columns to group by.
        aggs: Mapping of output column names to aggregation expressions.
            Supported functions: sum, avg, min, max, count.

    Returns:
        Aggregated table with group columns and aggregation results.

    Raises:
        ValueError: If group_by columns don't exist in table.

    Example:
        >>> engine.aggregate(
        ...     table,
        ...     group_by=["region"],
        ...     aggs={"total": "sum(amount)", "count": "count(*)"}
        ... )
    """
```

## Submitting Changes

### Pull Request Process

1. Update documentation for any new features
2. Add tests for your changes
3. Ensure all tests pass locally
4. Submit the pull request

### Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review of code performed
- [ ] Documentation updated
- [ ] Tests added and passing
- [ ] Commit messages follow Conventional Commits format
- [ ] Branch is up to date with main

### Automated Releases

When your PR is merged to `main`, the release workflow automatically:

1. Analyzes commit messages to determine version bump (major/minor/patch)
2. Updates version in `pyproject.toml` and `src/quicketl/_version.py`
3. Generates/updates `CHANGELOG.md`
4. Creates a Git tag and GitHub release
5. Publishes the package to PyPI

**No manual release steps required!** Just use proper commit messages.

## Style Guide

### Python Style

- Follow PEP 8 with line length of 100 characters
- Use ruff for linting and formatting
- Use type hints for all public APIs
- Prefer `from __future__ import annotations` for forward references

### Import Order

```python
# Standard library
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Third-party
import ibis
from pydantic import BaseModel

# Local
from quicketl.config.models import SourceConfig
from quicketl.logging import get_logger

if TYPE_CHECKING:
    import ibis.expr.types as ir
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | `PascalCase` | `PipelineConfig` |
| Functions/methods | `snake_case` | `run_pipeline` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_ENGINE` |
| Private members | `_leading_underscore` | `_parse_predicate` |

## Getting Help

- Open an issue for questions
- Check existing issues and discussions
- Read the documentation at https://quicketl.com

Thank you for contributing!
