"""Tests for quality checks.

Tests all 5 quality check types.
"""

from __future__ import annotations

import pytest

from quicketl.config.checks import (
    AcceptedValuesCheck,
    ExpressionCheck,
    NotNullCheck,
    RowCountCheck,
    UniqueCheck,
)
from quicketl.quality import run_check, run_checks


class TestNotNullCheck:
    """Tests for not_null check."""

    def test_not_null_pass(self, sample_data):
        """Check passes when no nulls."""
        config = NotNullCheck(columns=["id", "name", "amount"])
        result = run_check(sample_data, config)

        assert result.passed is True
        assert result.check_type == "not_null"

    def test_not_null_fail(self, sample_data_with_nulls):
        """Check fails when nulls present."""
        config = NotNullCheck(columns=["name", "amount"])
        result = run_check(sample_data_with_nulls, config)

        assert result.passed is False
        assert "null_counts" in result.details

    def test_not_null_missing_column(self, sample_data):
        """Check fails for missing column."""
        config = NotNullCheck(columns=["nonexistent"])
        result = run_check(sample_data, config)

        assert result.passed is False
        assert "not found" in result.message


class TestUniqueCheck:
    """Tests for unique check."""

    def test_unique_pass(self, sample_data):
        """Check passes when unique."""
        config = UniqueCheck(columns=["id"])
        result = run_check(sample_data, config)

        assert result.passed is True

    def test_unique_fail(self, sample_data_with_duplicates):
        """Check fails when duplicates exist."""
        config = UniqueCheck(columns=["id"])
        result = run_check(sample_data_with_duplicates, config)

        assert result.passed is False
        assert result.details["duplicate_count"] == 2

    def test_unique_composite(self, sample_data):
        """Check composite uniqueness."""
        config = UniqueCheck(columns=["id", "region"])
        result = run_check(sample_data, config)

        assert result.passed is True


class TestRowCountCheck:
    """Tests for row_count check."""

    def test_row_count_min_pass(self, sample_data):
        """Check passes when above minimum."""
        config = RowCountCheck(min=1)
        result = run_check(sample_data, config)

        assert result.passed is True

    def test_row_count_min_fail(self, sample_data):
        """Check fails when below minimum."""
        config = RowCountCheck(min=10)
        result = run_check(sample_data, config)

        assert result.passed is False
        assert "below minimum" in result.message

    def test_row_count_max_pass(self, sample_data):
        """Check passes when below maximum."""
        config = RowCountCheck(max=10)
        result = run_check(sample_data, config)

        assert result.passed is True

    def test_row_count_max_fail(self, sample_data):
        """Check fails when above maximum."""
        config = RowCountCheck(max=3)
        result = run_check(sample_data, config)

        assert result.passed is False
        assert "exceeds maximum" in result.message

    def test_row_count_range(self, sample_data):
        """Check with both min and max."""
        config = RowCountCheck(min=1, max=10)
        result = run_check(sample_data, config)

        assert result.passed is True


class TestAcceptedValuesCheck:
    """Tests for accepted_values check."""

    def test_accepted_values_pass(self, sample_data):
        """Check passes when all values accepted."""
        config = AcceptedValuesCheck(
            column="region",
            values=["North", "South", "East", "West"],
        )
        result = run_check(sample_data, config)

        assert result.passed is True

    def test_accepted_values_fail(self, sample_data):
        """Check fails when unexpected values present."""
        config = AcceptedValuesCheck(
            column="region",
            values=["North", "South"],  # Missing "East"
        )
        result = run_check(sample_data, config)

        assert result.passed is False
        assert "East" in result.details["unexpected_values"]

    def test_accepted_values_missing_column(self, sample_data):
        """Check fails for missing column."""
        config = AcceptedValuesCheck(column="nonexistent", values=["a", "b"])
        result = run_check(sample_data, config)

        assert result.passed is False
        assert "not found" in result.message


class TestExpressionCheck:
    """Tests for expression check."""

    def test_expression_pass(self, sample_data):
        """Check passes when expression true for all rows."""
        config = ExpressionCheck(expr="amount > 0")
        result = run_check(sample_data, config)

        assert result.passed is True

    def test_expression_fail(self, sample_data):
        """Check fails when expression false for some rows."""
        config = ExpressionCheck(expr="amount > 200")
        result = run_check(sample_data, config)

        assert result.passed is False
        assert result.details["failing_rows"] == 3  # 100, 200, 150

    def test_expression_complex(self, sample_data):
        """Check with complex expression."""
        config = ExpressionCheck(expr="amount > 50 AND active == true")
        result = run_check(sample_data, config)

        # Should fail for inactive row (Charlie with amount=150)
        assert result.passed is False


class TestRunChecks:
    """Tests for running multiple checks."""

    def test_run_multiple_checks_all_pass(self, sample_data):
        """All checks pass."""
        checks = [
            NotNullCheck(columns=["id"]),
            UniqueCheck(columns=["id"]),
            RowCountCheck(min=1),
        ]
        result = run_checks(sample_data, checks)

        assert result.all_passed is True
        assert result.passed_checks == 3
        assert result.failed_checks == 0

    def test_run_multiple_checks_some_fail(self, sample_data_with_nulls):
        """Some checks fail."""
        checks = [
            NotNullCheck(columns=["name"]),  # Will fail
            RowCountCheck(min=1),  # Will pass
        ]
        result = run_checks(sample_data_with_nulls, checks)

        assert result.all_passed is False
        assert result.passed_checks == 1
        assert result.failed_checks == 1

    def test_run_checks_fail_fast(self, sample_data_with_nulls):
        """Stop on first failure with fail_fast."""
        checks = [
            NotNullCheck(columns=["name"]),  # Will fail
            RowCountCheck(min=1),  # Won't be executed
            UniqueCheck(columns=["id"]),  # Won't be executed
        ]
        result = run_checks(sample_data_with_nulls, checks, fail_fast=True)

        assert result.all_passed is False
        assert result.total_checks == 1  # Only first check ran

    def test_run_checks_empty_list(self, sample_data):
        """Handle empty check list."""
        result = run_checks(sample_data, [])

        assert result.all_passed is True
        assert result.total_checks == 0
