"""Expression parsing utilities.

Helpers for converting ETLX expression syntax to Ibis expressions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import ibis

if TYPE_CHECKING:
    import ibis.expr.types as ir


def parse_expression(expr: str) -> ir.Value:
    """Parse a SQL-like expression string to an Ibis expression.

    Uses Ibis's built-in SQL expression parsing via `ibis._.sql()`.

    Args:
        expr: SQL-like expression string

    Returns:
        Ibis expression

    Examples:
        >>> parse_expression("amount * 0.1")
        >>> parse_expression("COALESCE(discount, 0)")
        >>> parse_expression("CASE WHEN amount > 100 THEN 'high' ELSE 'low' END")
    """
    return ibis._.sql(expr)


def parse_predicate(predicate: str) -> ir.BooleanValue:
    """Parse a filter predicate string to an Ibis boolean expression.

    Args:
        predicate: SQL-like predicate string

    Returns:
        Ibis boolean expression

    Examples:
        >>> parse_predicate("amount > 100")
        >>> parse_predicate("status = 'active' AND amount > 0")
        >>> parse_predicate("name LIKE '%Smith%'")
    """
    return ibis._.sql(predicate)


def parse_aggregation(agg_expr: str) -> ir.Value:
    """Parse an aggregation expression.

    Args:
        agg_expr: Aggregation expression string

    Returns:
        Ibis aggregation expression

    Examples:
        >>> parse_aggregation("sum(amount)")
        >>> parse_aggregation("count(*)")
        >>> parse_aggregation("avg(price)")
    """
    return ibis._.sql(agg_expr)


# Common expression patterns for reference
EXPRESSION_EXAMPLES = {
    "arithmetic": [
        "quantity * unit_price",
        "amount / total * 100",
        "price + tax",
    ],
    "comparison": [
        "amount > 100",
        "status = 'active'",
        "date >= '2025-01-01'",
    ],
    "logical": [
        "amount > 100 AND status = 'active'",
        "category IN ('A', 'B', 'C')",
        "name LIKE '%smith%'",
    ],
    "null_handling": [
        "COALESCE(discount, 0)",
        "NULLIF(value, 0)",
        "amount IS NOT NULL",
    ],
    "conditional": [
        "CASE WHEN amount > 100 THEN 'high' ELSE 'low' END",
        "IF(active, 'yes', 'no')",
    ],
    "string": [
        "LOWER(name)",
        "UPPER(email)",
        "CONCAT(first_name, ' ', last_name)",
        "TRIM(name)",
        "SUBSTRING(code, 1, 3)",
    ],
    "date": [
        "DATE_TRUNC('month', created_at)",
        "EXTRACT(YEAR FROM date_col)",
        "date_col + INTERVAL '7 days'",
    ],
    "aggregation": [
        "sum(amount)",
        "count(*)",
        "avg(price)",
        "min(date)",
        "max(value)",
        "count(DISTINCT customer_id)",
    ],
}
