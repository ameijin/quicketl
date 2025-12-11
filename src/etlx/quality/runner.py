"""Quality check execution and reporting.

Provides a runner to execute multiple checks and aggregate results.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ibis.expr.types as ir

from etlx.config.checks import CheckConfig
from etlx.logging import get_logger
from etlx.quality.checks import CheckResult, run_check

logger = get_logger(__name__)


@dataclass
class CheckSuiteResult:
    """Aggregated results from running multiple quality checks."""

    total_checks: int
    passed_checks: int
    failed_checks: int
    results: list[CheckResult]
    duration_ms: float
    all_passed: bool = field(init=False)

    def __post_init__(self) -> None:
        self.all_passed = self.failed_checks == 0

    @property
    def pass_rate(self) -> float:
        """Percentage of checks that passed."""
        if self.total_checks == 0:
            return 100.0
        return (self.passed_checks / self.total_checks) * 100

    def summary(self) -> str:
        """Return a summary string of the check results."""
        status = "PASSED" if self.all_passed else "FAILED"
        return (
            f"Check Suite {status}: "
            f"{self.passed_checks}/{self.total_checks} passed "
            f"({self.pass_rate:.1f}%) in {self.duration_ms:.1f}ms"
        )

    def __str__(self) -> str:
        lines = [self.summary(), ""]
        for result in self.results:
            lines.append(f"  {result}")
        return "\n".join(lines)


class CheckRunner:
    """Executes quality checks against a table.

    Examples:
        >>> runner = CheckRunner()
        >>> result = runner.run(table, checks)
        >>> if not result.all_passed:
        ...     raise ValueError(result.summary())
    """

    def __init__(self, fail_fast: bool = False) -> None:
        """Initialize the check runner.

        Args:
            fail_fast: Stop on first failure if True
        """
        self.fail_fast = fail_fast

    def run(
        self,
        table: ir.Table,
        checks: list[CheckConfig],
    ) -> CheckSuiteResult:
        """Run all quality checks against the table.

        Args:
            table: Ibis Table expression
            checks: List of check configurations

        Returns:
            CheckSuiteResult with aggregated results
        """
        start = time.perf_counter()
        results: list[CheckResult] = []
        passed = 0
        failed = 0

        for check in checks:
            logger.debug("running_check", check_type=check.type)

            try:
                result = run_check(table, check)
                results.append(result)

                if result.passed:
                    passed += 1
                    logger.info(
                        "check_passed",
                        check_type=check.type,
                        message=result.message,
                    )
                else:
                    failed += 1
                    logger.warning(
                        "check_failed",
                        check_type=check.type,
                        message=result.message,
                        details=result.details,
                    )

                    if self.fail_fast:
                        logger.info("fail_fast_triggered", check_type=check.type)
                        break

            except Exception as e:
                failed += 1
                error_result = CheckResult(
                    check_type=check.type,
                    passed=False,
                    message=f"Check execution error: {e}",
                    details={"error": str(e), "error_type": type(e).__name__},
                )
                results.append(error_result)
                logger.error(
                    "check_error",
                    check_type=check.type,
                    error=str(e),
                )

                if self.fail_fast:
                    break

        duration_ms = (time.perf_counter() - start) * 1000

        suite_result = CheckSuiteResult(
            total_checks=len(results),
            passed_checks=passed,
            failed_checks=failed,
            results=results,
            duration_ms=duration_ms,
        )

        logger.info(
            "check_suite_complete",
            total=suite_result.total_checks,
            passed=passed,
            failed=failed,
            all_passed=suite_result.all_passed,
            duration_ms=duration_ms,
        )

        return suite_result


def run_checks(
    table: ir.Table,
    checks: list[CheckConfig],
    fail_fast: bool = False,
) -> CheckSuiteResult:
    """Convenience function to run quality checks.

    Args:
        table: Ibis Table expression
        checks: List of check configurations
        fail_fast: Stop on first failure if True

    Returns:
        CheckSuiteResult

    Examples:
        >>> from etlx.config.checks import NotNullCheck, UniqueCheck
        >>> checks = [
        ...     NotNullCheck(columns=["id", "name"]),
        ...     UniqueCheck(columns=["id"]),
        ... ]
        >>> result = run_checks(table, checks)
        >>> assert result.all_passed
    """
    runner = CheckRunner(fail_fast=fail_fast)
    return runner.run(table, checks)
