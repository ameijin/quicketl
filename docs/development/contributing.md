# Contributing to QuickETL

Thank you for your interest in contributing to QuickETL! This guide will help you get started.

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- uv (recommended) or pip

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/quicketl.git
cd quicketl

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev,docs]"

# Run tests
pytest

# Run linting
ruff check src/
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/my-feature
```

### 2. Make Changes

- Write code following the style guide
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=quicketl --cov-report=html

# Run specific tests
pytest tests/test_transforms.py
```

### 4. Run Linting

```bash
# Check code style
ruff check src/

# Format code
ruff format src/
```

### 5. Submit Pull Request

- Push your branch
- Create a pull request
- Fill out the PR template
- Wait for review

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Write docstrings for public APIs
- Keep functions focused and small

### Example

```python
def apply_filter(
    table: Table,
    predicate: str,
) -> Table:
    """Apply a filter predicate to a table.

    Args:
        table: Input Ibis table.
        predicate: SQL-compatible filter expression.

    Returns:
        Filtered table.

    Raises:
        ValueError: If predicate is invalid.

    Example:
        >>> filtered = apply_filter(table, "amount > 100")
    """
    return table.filter(predicate)
```

## Testing

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_transforms.py   # Transform tests
├── test_checks.py       # Quality check tests
├── test_engine.py       # Engine tests
└── fixtures/            # Test data
```

### Writing Tests

```python
import pytest
from quicketl.transforms import FilterTransform

def test_filter_basic():
    """Test basic filter functionality."""
    transform = FilterTransform(predicate="amount > 0")
    result = transform.apply(sample_table)
    assert len(result) == expected_count

def test_filter_invalid_predicate():
    """Test filter with invalid predicate raises error."""
    with pytest.raises(ValueError):
        FilterTransform(predicate="invalid syntax >>>")
```

## Documentation

### Building Docs

```bash
# Serve locally
mkdocs serve

# Build static site
mkdocs build

# Check for errors
mkdocs build --strict
```

### Writing Docs

- Use clear, concise language
- Include examples
- Cross-link related pages
- Test code examples

## Pull Request Guidelines

### Title Format

```
feat: Add new transform for X
fix: Handle NULL values in filter
docs: Update quickstart guide
test: Add tests for aggregate transform
refactor: Simplify engine initialization
```

### PR Checklist

- [ ] Tests pass
- [ ] Linting passes
- [ ] Documentation updated
- [ ] Changelog entry added
- [ ] Linked to issue (if applicable)

## Issue Guidelines

### Bug Reports

Include:

- QuickETL version
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages

### Feature Requests

Include:

- Use case description
- Proposed solution
- Alternatives considered

## Getting Help

- Check existing issues
- Ask in discussions
- Read the documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
