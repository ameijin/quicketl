"""Tests for the _parse_predicate method in ETLXEngine.

This module tests predicate parsing for filter operations.
"""

from __future__ import annotations

import string

import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st

from quicketl.engines import ETLXEngine


@pytest.fixture
def engine():
    """Create a DuckDB engine for testing."""
    return ETLXEngine(backend="duckdb")


@pytest.fixture
def sample_table(engine):
    """Create a sample table for predicate testing."""
    data = {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", None, "Eve"],
        "amount": [100.0, 200.0, 150.0, 300.0, 250.0],
        "status": ["active", "pending", "active", "inactive", "active"],
        "active": [True, True, False, True, False],
        "score": [85, 92, None, 78, 88],
    }
    df = pd.DataFrame(data)
    return engine.connection.create_table("predicate_test", df, overwrite=True)


class TestComparisonOperators:
    """Tests for comparison operators in predicates."""

    def test_greater_than(self, engine, sample_table):
        """Test > operator."""
        result = engine._parse_predicate(sample_table, "amount > 150")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 3  # 200, 300, 250

    def test_less_than(self, engine, sample_table):
        """Test < operator."""
        result = engine._parse_predicate(sample_table, "amount < 200")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 2  # 100, 150

    def test_greater_than_or_equal(self, engine, sample_table):
        """Test >= operator."""
        result = engine._parse_predicate(sample_table, "amount >= 200")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 3  # 200, 300, 250

    def test_less_than_or_equal(self, engine, sample_table):
        """Test <= operator."""
        result = engine._parse_predicate(sample_table, "amount <= 150")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 2  # 100, 150

    def test_equal_double_equals(self, engine, sample_table):
        """Test == operator."""
        result = engine._parse_predicate(sample_table, "id == 3")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 1

    def test_equal_single_equals(self, engine, sample_table):
        """Test = operator (SQL style)."""
        result = engine._parse_predicate(sample_table, "id = 3")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 1

    def test_not_equal_exclamation(self, engine, sample_table):
        """Test != operator."""
        result = engine._parse_predicate(sample_table, "id != 3")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 4

    def test_not_equal_diamond(self, engine, sample_table):
        """Test <> operator (SQL style)."""
        result = engine._parse_predicate(sample_table, "id <> 3")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 4

    def test_string_comparison(self, engine, sample_table):
        """Test string comparison with quotes."""
        result = engine._parse_predicate(sample_table, "status = 'active'")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 3


class TestNullChecks:
    """Tests for NULL checking predicates."""

    def test_is_null(self, engine, sample_table):
        """Test IS NULL check."""
        result = engine._parse_predicate(sample_table, "name IS NULL")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 1

    def test_is_not_null(self, engine, sample_table):
        """Test IS NOT NULL check."""
        result = engine._parse_predicate(sample_table, "name IS NOT NULL")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 4

    def test_is_null_case_insensitive(self, engine, sample_table):
        """Test IS NULL is case insensitive."""
        result = engine._parse_predicate(sample_table, "name is null")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 1

    def test_is_not_null_case_insensitive(self, engine, sample_table):
        """Test IS NOT NULL is case insensitive."""
        result = engine._parse_predicate(sample_table, "score Is Not Null")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 4


class TestInOperator:
    """Tests for IN and NOT IN operators."""

    def test_in_with_strings(self, engine, sample_table):
        """Test IN with string values."""
        result = engine._parse_predicate(sample_table, "status IN ('active', 'pending')")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 4

    def test_in_with_numbers(self, engine, sample_table):
        """Test IN with numeric values."""
        result = engine._parse_predicate(sample_table, "id IN (1, 3, 5)")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 3

    def test_not_in_with_strings(self, engine, sample_table):
        """Test NOT IN with string values."""
        result = engine._parse_predicate(sample_table, "status NOT IN ('inactive')")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 4

    def test_not_in_with_numbers(self, engine, sample_table):
        """Test NOT IN with numeric values."""
        result = engine._parse_predicate(sample_table, "id NOT IN (2, 4)")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 3

    def test_in_case_insensitive(self, engine, sample_table):
        """Test IN is case insensitive."""
        result = engine._parse_predicate(sample_table, "id in (1, 2)")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 2


class TestLikeOperator:
    """Tests for LIKE pattern matching."""

    def test_like_starts_with(self, engine, sample_table):
        """Test LIKE with prefix pattern."""
        result = engine._parse_predicate(sample_table, "name LIKE 'A%'")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 1  # Alice

    def test_like_ends_with(self, engine, sample_table):
        """Test LIKE with suffix pattern."""
        result = engine._parse_predicate(sample_table, "name LIKE '%e'")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 3  # Alice, Charlie, Eve

    def test_like_contains(self, engine, sample_table):
        """Test LIKE with contains pattern."""
        result = engine._parse_predicate(sample_table, "name LIKE '%li%'")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 2  # Alice, Charlie

    def test_like_case_insensitive_keyword(self, engine, sample_table):
        """Test LIKE keyword is case insensitive."""
        result = engine._parse_predicate(sample_table, "name like 'B%'")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 1  # Bob


class TestBooleanColumns:
    """Tests for boolean column references."""

    def test_boolean_column_true(self, engine, sample_table):
        """Test boolean column as predicate."""
        result = engine._parse_predicate(sample_table, "active")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 3

    def test_boolean_column_not(self, engine, sample_table):
        """Test NOT with boolean column."""
        result = engine._parse_predicate(sample_table, "NOT active")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 2


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_whitespace_handling(self, engine, sample_table):
        """Test predicates with extra whitespace."""
        result = engine._parse_predicate(sample_table, "  amount > 150  ")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 3

    def test_invalid_predicate_raises_error(self, engine, sample_table):
        """Test invalid predicate raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            engine._parse_predicate(sample_table, "invalid predicate syntax")
        assert "Unable to parse predicate" in str(exc_info.value)

    def test_float_comparison(self, engine, sample_table):
        """Test comparison with float values."""
        result = engine._parse_predicate(sample_table, "amount > 149.99")
        filtered = sample_table.filter(result)
        assert engine.row_count(filtered) == 4  # 150, 200, 300, 250


class TestParseValue:
    """Tests for the _parse_value helper method."""

    def test_parse_single_quoted_string(self, engine):
        """Test parsing single-quoted string."""
        assert engine._parse_value("'hello'") == "hello"

    def test_parse_double_quoted_string(self, engine):
        """Test parsing double-quoted string."""
        assert engine._parse_value('"world"') == "world"

    def test_parse_integer(self, engine):
        """Test parsing integer."""
        assert engine._parse_value("42") == 42

    def test_parse_negative_integer(self, engine):
        """Test parsing negative integer."""
        assert engine._parse_value("-10") == -10

    def test_parse_float(self, engine):
        """Test parsing float."""
        assert engine._parse_value("3.14") == 3.14

    def test_parse_negative_float(self, engine):
        """Test parsing negative float."""
        assert engine._parse_value("-2.5") == -2.5

    def test_parse_true(self, engine):
        """Test parsing boolean true."""
        assert engine._parse_value("true") is True
        assert engine._parse_value("True") is True
        assert engine._parse_value("TRUE") is True

    def test_parse_false(self, engine):
        """Test parsing boolean false."""
        assert engine._parse_value("false") is False
        assert engine._parse_value("False") is False
        assert engine._parse_value("FALSE") is False


# ============================================================================
# Property-Based Tests with Hypothesis
# ============================================================================


class TestPredicateParsingWithHypothesis:
    """Property-based tests for predicate parsing using hypothesis."""

    @pytest.mark.hypothesis
    @given(st.integers(min_value=-1000000, max_value=1000000))
    @settings(max_examples=50)
    def test_numeric_comparison_never_raises(self, value):
        """Any integer should work in numeric comparison."""
        engine = ETLXEngine(backend="duckdb")
        df = pd.DataFrame({"n": [value, value + 1, value - 1]})
        table = engine.connection.create_table("hyp_test", df, overwrite=True)

        # Should not raise
        expr = engine._parse_predicate(table, f"n > {value - 1}")
        # Verify it's a valid expression
        result = table.filter(expr)
        assert engine.row_count(result) >= 0

    @pytest.mark.hypothesis
    @given(st.floats(min_value=-1e4, max_value=1e4, allow_nan=False, allow_infinity=False).filter(
        lambda x: abs(x) >= 0.001 or x == 0  # Avoid scientific notation for tiny numbers
    ))
    @settings(max_examples=50)
    def test_float_comparison_never_raises(self, value):
        """Any reasonable float should work in numeric comparison."""
        engine = ETLXEngine(backend="duckdb")
        df = pd.DataFrame({"n": [value, value + 0.1, value - 0.1]})
        table = engine.connection.create_table("hyp_float_test", df, overwrite=True)

        # Format with fixed notation to avoid scientific notation issues
        value_str = f"{value:.6f}"
        expr = engine._parse_predicate(table, f"n >= {value_str}")
        result = table.filter(expr)
        assert engine.row_count(result) >= 0

    @pytest.mark.hypothesis
    @given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=20))
    @settings(max_examples=50)
    def test_quoted_string_values_parse_correctly(self, text):
        """Any alphabetic string should parse as a value."""
        engine = ETLXEngine(backend="duckdb")

        # Should parse without error
        result = engine._parse_value(f"'{text}'")
        assert result == text

    @pytest.mark.hypothesis
    @given(st.integers())
    @settings(max_examples=50)
    def test_integer_parsing_roundtrips(self, value):
        """Integers should parse to the same integer value."""
        engine = ETLXEngine(backend="duckdb")
        result = engine._parse_value(str(value))
        assert result == value

    @pytest.mark.hypothesis
    @given(st.sampled_from(["true", "True", "TRUE", "false", "False", "FALSE"]))
    def test_boolean_parsing_case_insensitive(self, bool_str):
        """Boolean strings should parse regardless of case."""
        engine = ETLXEngine(backend="duckdb")
        result = engine._parse_value(bool_str)
        assert result is (bool_str.lower() == "true")
