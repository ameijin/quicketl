"""ETLX quality checks.

Provides data quality validation using Ibis expressions.
"""

from quicketl.quality.checks import (
    CheckResult,
    run_accepted_values_check,
    run_check,
    run_expression_check,
    run_not_null_check,
    run_row_count_check,
    run_unique_check,
)
from quicketl.quality.runner import CheckRunner, CheckSuiteResult, run_checks

__all__ = [
    # Check results
    "CheckResult",
    "CheckSuiteResult",
    # Individual check functions
    "run_not_null_check",
    "run_unique_check",
    "run_row_count_check",
    "run_accepted_values_check",
    "run_expression_check",
    "run_check",
    # Runner
    "CheckRunner",
    "run_checks",
]
