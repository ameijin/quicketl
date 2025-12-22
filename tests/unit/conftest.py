"""Unit test fixtures and configuration.

Unit tests should be fast (<100ms) and isolated from external dependencies.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CLI test runner for testing Typer commands."""
    return CliRunner()


@pytest.fixture
def mock_engine(mocker):
    """Create a mock ETLXEngine for unit tests that don't need real execution."""
    from quicketl.engines import ETLXEngine

    mock = mocker.Mock(spec=ETLXEngine)
    mock.backend = "duckdb"
    return mock
