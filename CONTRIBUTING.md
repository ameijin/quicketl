# Contributing to QuickETL

Thank you for your interest in contributing to QuickETL! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
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

## Testing

### Test Requirements

- All new features must have tests
- All bug fixes should have regression tests
- Maintain >80% code coverage
- Tests must pass on all supported Python versions

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── fixtures/            # Test data files
├── test_transforms.py   # Transform tests
├── test_checks.py       # Quality check tests
├── test_pipeline.py     # Pipeline tests
├── test_engine.py       # Engine tests
└── test_cli.py          # CLI tests
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
