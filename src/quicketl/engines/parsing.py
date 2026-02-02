"""Shared predicate and value parsing utilities.

Used by both the engine (transforms) and quality checks to parse
SQL-like predicate strings into Ibis expressions.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import ibis

if TYPE_CHECKING:
    import ibis.expr.types as ir


def parse_value(val_str: str) -> Any:
    """Parse a string value into the appropriate Python type.

    Args:
        val_str: Raw string value

    Returns:
        Parsed value (str, int, float, or bool)

    Examples:
        >>> parse_value("'hello'")
        'hello'
        >>> parse_value("42")
        42
        >>> parse_value("3.14")
        3.14
        >>> parse_value("true")
        True
    """
    val_str = val_str.strip()

    # Handle quoted strings
    if (val_str.startswith("'") and val_str.endswith("'")) or \
       (val_str.startswith('"') and val_str.endswith('"')):
        return val_str[1:-1]

    # Handle booleans
    if val_str.lower() in ("true", "false"):
        return val_str.lower() == "true"

    # Handle numbers
    try:
        if "." in val_str:
            return float(val_str)
        return int(val_str)
    except ValueError:
        return val_str


def parse_predicate(table: ir.Table, predicate: str) -> ibis.Expr:
    """Parse a simple SQL-like predicate into an Ibis expression.

    Supported predicates:
        - Comparison: col > 100, col == 'value', col != 0
        - IN: col IN ('a', 'b', 'c'), col IN (1, 2, 3)
        - NOT IN: col NOT IN ('x', 'y')
        - NULL checks: col IS NULL, col IS NOT NULL
        - LIKE: col LIKE '%pattern%'
        - Boolean: active, NOT active

    Args:
        table: Ibis Table to resolve column references against
        predicate: SQL-like predicate string

    Returns:
        Ibis expression that can be used with table.filter()

    Raises:
        ValueError: If the predicate cannot be parsed
    """
    predicate = predicate.strip()
    predicate_lower = predicate.lower()

    # Handle IS NULL and IS NOT NULL
    is_null_match = re.match(r"(\w+)\s+IS\s+NULL", predicate, re.I)
    if is_null_match:
        return table[is_null_match.group(1)].isnull()

    is_not_null_match = re.match(r"(\w+)\s+IS\s+NOT\s+NULL", predicate, re.I)
    if is_not_null_match:
        return table[is_not_null_match.group(1)].notnull()

    # Handle NOT IN (col NOT IN (val1, val2, ...))
    not_in_match = re.match(r"(\w+)\s+NOT\s+IN\s*\((.+)\)", predicate, re.I)
    if not_in_match:
        col_name = not_in_match.group(1)
        values_str = not_in_match.group(2)
        values = [parse_value(v.strip()) for v in values_str.split(",")]
        return ~table[col_name].isin(values)

    # Handle IN (col IN (val1, val2, ...))
    in_match = re.match(r"(\w+)\s+IN\s*\((.+)\)", predicate, re.I)
    if in_match:
        col_name = in_match.group(1)
        values_str = in_match.group(2)
        values = [parse_value(v.strip()) for v in values_str.split(",")]
        return table[col_name].isin(values)

    # Handle LIKE pattern matching
    like_match = re.match(r"(\w+)\s+LIKE\s+'(.+)'", predicate, re.I)
    if like_match:
        col_name = like_match.group(1)
        pattern = like_match.group(2)
        return table[col_name].like(pattern)

    # Handle comparison operators (longest operators first to avoid partial matches)
    for op_str, op_func in [
        (">=", lambda col, val: col >= val),
        ("<=", lambda col, val: col <= val),
        ("!=", lambda col, val: col != val),
        ("<>", lambda col, val: col != val),  # SQL not equal
        ("==", lambda col, val: col == val),
        (">", lambda col, val: col > val),
        ("<", lambda col, val: col < val),
        ("=", lambda col, val: col == val),  # Single = must be last
    ]:
        if op_str in predicate:
            # Split only once to handle the operator correctly
            parts = predicate.split(op_str, 1)
            if len(parts) == 2:
                col_name = parts[0].strip()
                val_str = parts[1].strip()

                val = parse_value(val_str)
                return op_func(table[col_name], val)

    # Handle boolean column references (e.g., "active" or "NOT active")
    if predicate_lower.startswith("not "):
        col_name = predicate[4:].strip()
        return ~table[col_name]
    elif predicate in table.columns:
        return table[predicate]

    raise ValueError(f"Unable to parse predicate: {predicate}")
