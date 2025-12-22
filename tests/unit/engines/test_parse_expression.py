"""Tests for the _parse_expression method in ETLXEngine.

This module tests expression parsing for derive_column operations.
"""

from __future__ import annotations

import string

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from quicketl.engines import ETLXEngine


@pytest.fixture
def engine():
    """Create a DuckDB engine for testing."""
    return ETLXEngine(backend="duckdb")


@pytest.fixture
def sample_table(engine):
    """Create a sample table for expression testing."""
    data = {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", None, "Eve"],
        "amount": [100.0, 200.0, 150.0, 300.0, 250.0],
        "tax_rate": [0.1, 0.15, 0.1, 0.2, 0.15],
        "first_name": ["  Alice  ", "Bob", "Charlie", "Diana", "Eve"],
        "last_name": ["Smith", "Jones", None, "Williams", "Brown"],
        "score": [85, -92, 0, -78, 88],
    }
    df = pd.DataFrame(data)
    return engine.connection.create_table("expr_test", df, overwrite=True)


class TestArithmeticOperators:
    """Tests for arithmetic operators in expressions."""

    def test_addition(self, engine, sample_table):
        """Test + operator."""
        expr = engine._parse_expression(sample_table, "amount + 50")
        result = sample_table.mutate(new_col=expr)
        df = engine.to_pandas(result)
        assert df["new_col"].iloc[0] == 150.0  # 100 + 50

    def test_subtraction(self, engine, sample_table):
        """Test - operator."""
        expr = engine._parse_expression(sample_table, "amount - 50")
        result = sample_table.mutate(new_col=expr)
        df = engine.to_pandas(result)
        assert df["new_col"].iloc[0] == 50.0  # 100 - 50

    def test_multiplication(self, engine, sample_table):
        """Test * operator."""
        expr = engine._parse_expression(sample_table, "amount * 2")
        result = sample_table.mutate(new_col=expr)
        df = engine.to_pandas(result)
        assert df["new_col"].iloc[0] == 200.0  # 100 * 2

    def test_division(self, engine, sample_table):
        """Test / operator."""
        expr = engine._parse_expression(sample_table, "amount / 2")
        result = sample_table.mutate(new_col=expr)
        df = engine.to_pandas(result)
        assert df["new_col"].iloc[0] == 50.0  # 100 / 2

    def test_column_arithmetic(self, engine, sample_table):
        """Test arithmetic with two columns."""
        expr = engine._parse_expression(sample_table, "amount * tax_rate")
        result = sample_table.mutate(tax_amount=expr)
        df = engine.to_pandas(result)
        assert df["tax_amount"].iloc[0] == 10.0  # 100 * 0.1


class TestStringFunctions:
    """Tests for string manipulation functions."""

    def test_upper(self, engine, sample_table):
        """Test UPPER function."""
        expr = engine._parse_expression(sample_table, "UPPER(name)")
        result = sample_table.mutate(upper_name=expr)
        df = engine.to_pandas(result)
        assert df["upper_name"].iloc[0] == "ALICE"

    def test_lower(self, engine, sample_table):
        """Test LOWER function."""
        expr = engine._parse_expression(sample_table, "LOWER(name)")
        result = sample_table.mutate(lower_name=expr)
        df = engine.to_pandas(result)
        assert df["lower_name"].iloc[0] == "alice"

    def test_trim(self, engine, sample_table):
        """Test TRIM function."""
        expr = engine._parse_expression(sample_table, "TRIM(first_name)")
        result = sample_table.mutate(trimmed=expr)
        df = engine.to_pandas(result)
        assert df["trimmed"].iloc[0] == "Alice"  # Spaces removed

    def test_length(self, engine, sample_table):
        """Test LENGTH function."""
        expr = engine._parse_expression(sample_table, "LENGTH(name)")
        result = sample_table.mutate(name_len=expr)
        df = engine.to_pandas(result)
        assert df["name_len"].iloc[0] == 5  # "Alice" has 5 chars

    def test_concat(self, engine, sample_table):
        """Test CONCAT function."""
        expr = engine._parse_expression(sample_table, "CONCAT(name, last_name)")
        result = sample_table.mutate(full_name=expr)
        df = engine.to_pandas(result)
        assert df["full_name"].iloc[0] == "AliceSmith"


class TestNullHandlingFunctions:
    """Tests for NULL handling functions."""

    def test_coalesce_with_null(self, engine, sample_table):
        """Test COALESCE returns first non-null value."""
        expr = engine._parse_expression(sample_table, "COALESCE(name, 'Unknown')")
        result = sample_table.mutate(safe_name=expr)
        df = engine.to_pandas(result)
        # Row with null name should show 'Unknown'
        assert df["safe_name"].iloc[3] == "Unknown"
        # Row with name should show the name
        assert df["safe_name"].iloc[0] == "Alice"

    def test_coalesce_multiple_args(self, engine, sample_table):
        """Test COALESCE with multiple arguments."""
        expr = engine._parse_expression(sample_table, "COALESCE(last_name, name, 'N/A')")
        result = sample_table.mutate(display_name=expr)
        df = engine.to_pandas(result)
        # First row has last_name
        assert df["display_name"].iloc[0] == "Smith"

    def test_nullif(self, engine, sample_table):
        """Test NULLIF returns NULL when values match."""
        # Create a table with specific values for testing NULLIF
        data = {"val": [1, 2, 1, 3]}
        df = pd.DataFrame(data)
        table = engine.connection.create_table("nullif_test", df, overwrite=True)

        expr = engine._parse_expression(table, "NULLIF(val, 1)")
        result = table.mutate(nullified=expr)
        df_result = engine.to_pandas(result)
        # Value 1 should become NULL
        assert pd.isna(df_result["nullified"].iloc[0])
        assert df_result["nullified"].iloc[1] == 2


class TestNumericFunctions:
    """Tests for numeric functions."""

    def test_abs_positive(self, engine, sample_table):
        """Test ABS with positive values."""
        expr = engine._parse_expression(sample_table, "ABS(score)")
        result = sample_table.mutate(abs_score=expr)
        df = engine.to_pandas(result)
        assert df["abs_score"].iloc[0] == 85

    def test_abs_negative(self, engine, sample_table):
        """Test ABS with negative values."""
        expr = engine._parse_expression(sample_table, "ABS(score)")
        result = sample_table.mutate(abs_score=expr)
        df = engine.to_pandas(result)
        assert df["abs_score"].iloc[1] == 92  # -92 becomes 92

    def test_round_no_decimals(self, engine):
        """Test ROUND with no decimal places."""
        data = {"val": [1.4, 1.5, 1.6, 2.5]}
        df = pd.DataFrame(data)
        table = engine.connection.create_table("round_test", df, overwrite=True)

        expr = engine._parse_expression(table, "ROUND(val)")
        result = table.mutate(rounded=expr)
        df_result = engine.to_pandas(result)
        assert df_result["rounded"].iloc[0] == 1
        assert df_result["rounded"].iloc[2] == 2

    def test_round_with_decimals(self, engine):
        """Test ROUND with specified decimal places."""
        data = {"val": [1.234, 2.567, 3.891]}
        df = pd.DataFrame(data)
        table = engine.connection.create_table("round_test2", df, overwrite=True)

        expr = engine._parse_expression(table, "ROUND(val, 2)")
        result = table.mutate(rounded=expr)
        df_result = engine.to_pandas(result)
        assert df_result["rounded"].iloc[0] == 1.23


class TestColumnReferences:
    """Tests for simple column references."""

    def test_column_reference(self, engine, sample_table):
        """Test direct column reference."""
        expr = engine._parse_expression(sample_table, "name")
        result = sample_table.mutate(name_copy=expr)
        df = engine.to_pandas(result)
        assert df["name_copy"].iloc[0] == "Alice"

    def test_literal_value(self, engine, sample_table):
        """Test literal value expression."""
        expr = engine._parse_expression(sample_table, "42")
        result = sample_table.mutate(constant=expr)
        df = engine.to_pandas(result)
        assert df["constant"].iloc[0] == 42

    def test_literal_string(self, engine, sample_table):
        """Test literal string expression."""
        expr = engine._parse_expression(sample_table, "'constant'")
        result = sample_table.mutate(constant=expr)
        df = engine.to_pandas(result)
        assert df["constant"].iloc[0] == "constant"


class TestCaseInsensitivity:
    """Tests for case insensitivity of function names."""

    def test_upper_lowercase_function(self, engine, sample_table):
        """Test UPPER function with lowercase."""
        expr = engine._parse_expression(sample_table, "upper(name)")
        result = sample_table.mutate(upper_name=expr)
        df = engine.to_pandas(result)
        assert df["upper_name"].iloc[0] == "ALICE"

    def test_coalesce_mixed_case(self, engine, sample_table):
        """Test COALESCE with mixed case."""
        expr = engine._parse_expression(sample_table, "Coalesce(name, 'X')")
        result = sample_table.mutate(safe_name=expr)
        df = engine.to_pandas(result)
        assert df["safe_name"].iloc[0] == "Alice"


# ============================================================================
# Property-Based Tests with Hypothesis
# ============================================================================


class TestExpressionParsingWithHypothesis:
    """Property-based tests for expression parsing using hypothesis."""

    @pytest.mark.hypothesis
    @given(st.integers(min_value=1, max_value=1000))
    @settings(max_examples=50)
    def test_multiplication_by_integer(self, multiplier):
        """Multiplying a column by any positive integer should work."""
        engine = ETLXEngine(backend="duckdb")
        df = pd.DataFrame({"val": [10.0, 20.0, 30.0]})
        table = engine.connection.create_table("hyp_mult", df, overwrite=True)

        expr = engine._parse_expression(table, f"val * {multiplier}")
        result = table.mutate(product=expr)
        df_result = engine.to_pandas(result)

        # Verify calculation is correct
        assert df_result["product"].iloc[0] == 10.0 * multiplier

    @pytest.mark.hypothesis
    @given(st.floats(min_value=0.01, max_value=100, allow_nan=False, allow_infinity=False))
    @settings(max_examples=50)
    def test_division_by_positive_float(self, divisor):
        """Dividing a column by any positive float should work."""
        engine = ETLXEngine(backend="duckdb")
        df = pd.DataFrame({"val": [100.0, 200.0, 300.0]})
        table = engine.connection.create_table("hyp_div", df, overwrite=True)

        expr = engine._parse_expression(table, f"val / {divisor}")
        result = table.mutate(quotient=expr)
        df_result = engine.to_pandas(result)

        # Verify calculation is approximately correct
        assert abs(df_result["quotient"].iloc[0] - (100.0 / divisor)) < 0.0001

    @pytest.mark.hypothesis
    @given(st.integers(min_value=-1000000, max_value=1000000))
    @settings(max_examples=50)
    def test_addition_with_integer(self, addend):
        """Adding any integer to a column should work."""
        engine = ETLXEngine(backend="duckdb")
        df = pd.DataFrame({"val": [50]})
        table = engine.connection.create_table("hyp_add", df, overwrite=True)

        expr = engine._parse_expression(table, f"val + {addend}")
        result = table.mutate(sum=expr)
        df_result = engine.to_pandas(result)

        assert df_result["sum"].iloc[0] == 50 + addend

    @pytest.mark.hypothesis
    @given(st.text(alphabet=string.ascii_letters + string.digits + " ", min_size=1, max_size=50))
    @settings(max_examples=50)
    def test_literal_string_parsing(self, text):
        """Any safe string literal should parse correctly."""
        engine = ETLXEngine(backend="duckdb")
        df = pd.DataFrame({"id": [1]})
        table = engine.connection.create_table("hyp_str", df, overwrite=True)

        # Escape single quotes in the text
        safe_text = text.replace("'", "''")
        expr = engine._parse_expression(table, f"'{safe_text}'")
        result = table.mutate(str_val=expr)
        df_result = engine.to_pandas(result)

        # The result should contain the original text
        assert df_result["str_val"].iloc[0] == text
