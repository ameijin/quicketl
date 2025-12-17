"""ETLXEngine - Core engine wrapper around Ibis.

This module provides the main abstraction layer that wraps Ibis backends,
exposing a simplified, ETL-focused API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import ibis

from quicketl.config.models import DatabaseSource, FileSource, SinkConfig, SourceConfig
from quicketl.config.transforms import (
    AggregateTransform,
    CastTransform,
    DedupTransform,
    DeriveColumnTransform,
    FillNullTransform,
    FilterTransform,
    JoinTransform,
    LimitTransform,
    RenameTransform,
    SelectTransform,
    SortTransform,
    TransformStep,
    UnionTransform,
)
from quicketl.logging import get_logger

if TYPE_CHECKING:
    import ibis.expr.types as ir
    import pandas as pd
    import polars as pl

log = get_logger(__name__)


@dataclass
class WriteResult:
    """Result of a write operation."""

    rows_written: int
    path: str | None = None
    table: str | None = None
    duration_ms: float = 0.0


class ETLXEngine:
    """ETLX engine wrapper around Ibis.

    Provides a simplified, ETL-focused API for data processing with support
    for 20+ backends via Ibis.

    Example:
        >>> engine = ETLXEngine(backend="duckdb")
        >>> table = engine.read_file("data.parquet", "parquet")
        >>> filtered = engine.filter(table, "amount > 100")
        >>> result = engine.to_polars(filtered)
    """

    def __init__(
        self,
        backend: str = "duckdb",
        connection_string: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the engine with the specified backend.

        Args:
            backend: Backend name (duckdb, polars, datafusion, spark, etc.)
            connection_string: Optional connection string for database backends
            **kwargs: Additional arguments passed to ibis.connect()
        """
        self._backend_name = backend
        self._kwargs = kwargs

        # Connect to backend
        if connection_string:
            self._con = ibis.connect(connection_string, **kwargs)
        else:
            # Use in-memory connection for local backends
            self._con = self._create_connection(backend, **kwargs)

        log.debug("engine_initialized", backend=backend)

    def _create_connection(self, backend: str, **kwargs: Any) -> ibis.BaseBackend:
        """Create an Ibis connection for the specified backend."""
        match backend:
            case "duckdb":
                return ibis.duckdb.connect(**kwargs)
            case "polars":
                return ibis.polars.connect(**kwargs)
            case "datafusion":
                return ibis.datafusion.connect(**kwargs)
            case "pandas":
                return ibis.pandas.connect(**kwargs)
            case _:
                # Try generic connect for other backends
                return ibis.connect(f"{backend}://", **kwargs)

    @property
    def backend_name(self) -> str:
        """Get the backend name."""
        return self._backend_name

    @property
    def connection(self) -> ibis.BaseBackend:
        """Get the underlying Ibis connection."""
        return self._con

    # =========================================================================
    # IO Operations
    # =========================================================================

    def read_source(self, config: SourceConfig) -> ir.Table:
        """Read data from a configured source.

        Args:
            config: Source configuration

        Returns:
            Ibis Table expression
        """
        match config:
            case FileSource(path=path, format=fmt, options=opts):
                return self.read_file(path, fmt, **opts)
            case DatabaseSource(connection=conn, query=query, table=table):
                return self.read_database(conn, query, table)
            case _:
                raise NotImplementedError(f"Source type not supported: {type(config)}")

    def read_file(
        self,
        path: str,
        format: str,
        **options: Any,
    ) -> ir.Table:
        """Read data from a file.

        Args:
            path: File path (local or cloud URI)
            format: File format (parquet, csv, json)
            **options: Format-specific read options

        Returns:
            Ibis Table expression
        """
        log.debug("reading_file", path=path, format=format)

        match format:
            case "parquet":
                return self._con.read_parquet(path, **options)
            case "csv":
                return self._con.read_csv(path, **options)
            case "json":
                return self._con.read_json(path, **options)
            case _:
                raise ValueError(f"Unsupported file format: {format}")

    def read_database(
        self,
        connection: str,
        query: str | None = None,
        table: str | None = None,
    ) -> ir.Table:
        """Read data from a database.

        Args:
            connection: Connection string
            query: SQL query to execute
            table: Table name (alternative to query)

        Returns:
            Ibis Table expression
        """
        log.debug("reading_database", has_query=query is not None, table=table)

        # For database reads, we may need a separate connection
        db_con = ibis.connect(connection)

        if query:
            return db_con.sql(query)
        elif table:
            return db_con.table(table)
        else:
            raise ValueError("Either query or table must be provided")

    def write_sink(
        self,
        table: ir.Table,
        config: SinkConfig,
    ) -> WriteResult:
        """Write data to a configured sink.

        Args:
            table: Ibis Table expression
            config: Sink configuration

        Returns:
            WriteResult with operation details
        """
        from quicketl.config.models import DatabaseSink, FileSink

        match config:
            case FileSink(path=path, format=fmt, partition_by=parts):
                return self.write_file(table, path, fmt, partition_by=parts)
            case DatabaseSink(connection=conn, table=target_table, mode=mode):
                return self.write_database(table, conn, target_table, mode=mode)
            case _:
                raise NotImplementedError(f"Sink type not supported: {type(config)}")

    def write_file(
        self,
        table: ir.Table,
        path: str,
        format: str = "parquet",
        partition_by: list[str] | None = None,
    ) -> WriteResult:
        """Write data to a file.

        Args:
            table: Ibis Table expression
            path: Output path
            format: Output format (parquet, csv)
            partition_by: Columns to partition by

        Returns:
            WriteResult with operation details
        """
        from quicketl.io.writers.file import write_file

        log.debug("writing_file", path=path, format=format, partition_by=partition_by)

        result = write_file(table, path, format, partition_by=partition_by)

        return WriteResult(
            rows_written=result.rows_written,
            path=result.path,
            duration_ms=result.duration_ms,
        )

    def write_database(
        self,
        table: ir.Table,
        connection: str,
        target_table: str,
        mode: Literal["append", "truncate", "replace", "upsert"] = "append",
    ) -> WriteResult:
        """Write data to a database table.

        Args:
            table: Ibis Table expression
            connection: Database connection string
            target_table: Target table name (can include schema, e.g., 'gold.revenue')
            mode: Write mode - 'append', 'truncate', or 'replace'

        Returns:
            WriteResult with operation details

        Example:
            >>> engine.write_database(
            ...     table,
            ...     "postgresql://user:pass@localhost/db",
            ...     "gold.revenue_summary",
            ...     mode="truncate"
            ... )
        """
        from quicketl.io.writers.database import write_database

        log.debug("writing_database", table=target_table, mode=mode)

        result = write_database(
            table,
            connection=connection,
            target_table=target_table,
            mode=mode,
        )

        return WriteResult(
            rows_written=result.rows_written,
            table=result.table,
            duration_ms=result.duration_ms,
        )

    # =========================================================================
    # Transform Operations (12 total)
    # =========================================================================

    def select(self, table: ir.Table, columns: list[str]) -> ir.Table:
        """Select specific columns.

        Args:
            table: Input table
            columns: Column names to select

        Returns:
            Table with only selected columns
        """
        return table.select(columns)

    def rename(self, table: ir.Table, mapping: dict[str, str]) -> ir.Table:
        """Rename columns.

        Args:
            table: Input table
            mapping: Old name -> new name mapping

        Returns:
            Table with renamed columns
        """
        # Ibis expects {new_name: old_name}, so we need to swap
        ibis_mapping = {new: old for old, new in mapping.items()}
        return table.rename(ibis_mapping)

    def filter(self, table: ir.Table, predicate: str) -> ir.Table:
        """Filter rows using a SQL-like predicate.

        Args:
            table: Input table
            predicate: SQL-like filter expression (e.g., "amount > 100")

        Returns:
            Filtered table
        """
        # Parse simple predicates into Ibis expressions
        expr = self._parse_predicate(table, predicate)
        return table.filter(expr)

    def _parse_predicate(self, table: ir.Table, predicate: str) -> ibis.Expr:
        """Parse a simple SQL-like predicate into an Ibis expression.

        Supported predicates:
            - Comparison: col > 100, col == 'value', col != 0
            - IN: col IN ('a', 'b', 'c'), col IN (1, 2, 3)
            - NOT IN: col NOT IN ('x', 'y')
            - NULL checks: col IS NULL, col IS NOT NULL
            - Boolean: active, NOT active
        """
        import re

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
            values = [self._parse_value(v.strip()) for v in values_str.split(",")]
            return ~table[col_name].isin(values)

        # Handle IN (col IN (val1, val2, ...))
        in_match = re.match(r"(\w+)\s+IN\s*\((.+)\)", predicate, re.I)
        if in_match:
            col_name = in_match.group(1)
            values_str = in_match.group(2)
            values = [self._parse_value(v.strip()) for v in values_str.split(",")]
            return table[col_name].isin(values)

        # Handle LIKE pattern matching
        like_match = re.match(r"(\w+)\s+LIKE\s+'(.+)'", predicate, re.I)
        if like_match:
            col_name = like_match.group(1)
            pattern = like_match.group(2)
            return table[col_name].like(pattern)

        # Handle comparison operators (check longest operators first to avoid partial matches)
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

                    # Parse the value
                    val = self._parse_value(val_str)
                    return op_func(table[col_name], val)

        # Handle boolean column references (e.g., "active" or "NOT active")
        if predicate_lower.startswith("not "):
            col_name = predicate[4:].strip()
            return ~table[col_name]
        elif predicate in table.columns:
            return table[predicate]

        raise ValueError(f"Unable to parse predicate: {predicate}")

    def _parse_value(self, val_str: str) -> Any:
        """Parse a string value into the appropriate Python type."""
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

    def _parse_expression(self, table: ir.Table, expr: str) -> ibis.Expr:
        """Parse a simple SQL-like expression into an Ibis expression.

        Supported expressions:
            - Arithmetic: amount * 2, price + tax, a / b, a - b
            - Functions: coalesce(col1, col2, default), nullif(col, value)
            - Column references: column_name
            - Literals: 123, 'string', 3.14
        """
        import re

        expr = expr.strip()

        # Handle COALESCE(col1, col2, ..., default)
        coalesce_match = re.match(r"coalesce\s*\((.+)\)", expr, re.I)
        if coalesce_match:
            args_str = coalesce_match.group(1)
            # Split by comma, but handle nested parentheses
            args = self._split_args(args_str)
            ibis_args = [self._parse_operand(table, a) for a in args]
            return ibis.coalesce(*ibis_args)

        # Handle NULLIF(col, value)
        nullif_match = re.match(r"nullif\s*\((.+?),\s*(.+)\)", expr, re.I)
        if nullif_match:
            col_expr = self._parse_operand(table, nullif_match.group(1).strip())
            val_expr = self._parse_operand(table, nullif_match.group(2).strip())
            return col_expr.nullif(val_expr)

        # Handle CONCAT(col1, col2, ...)
        concat_match = re.match(r"concat\s*\((.+)\)", expr, re.I)
        if concat_match:
            args = self._split_args(concat_match.group(1))
            result = self._parse_operand(table, args[0])
            for arg in args[1:]:
                result = result.concat(self._parse_operand(table, arg))
            return result

        # Handle UPPER(col) and LOWER(col)
        upper_match = re.match(r"upper\s*\(\s*(\w+)\s*\)", expr, re.I)
        if upper_match:
            return table[upper_match.group(1)].upper()

        lower_match = re.match(r"lower\s*\(\s*(\w+)\s*\)", expr, re.I)
        if lower_match:
            return table[lower_match.group(1)].lower()

        # Handle TRIM(col)
        trim_match = re.match(r"trim\s*\(\s*(\w+)\s*\)", expr, re.I)
        if trim_match:
            return table[trim_match.group(1)].strip()

        # Handle LENGTH(col)
        length_match = re.match(r"length\s*\(\s*(\w+)\s*\)", expr, re.I)
        if length_match:
            return table[length_match.group(1)].length()

        # Handle ABS(col)
        abs_match = re.match(r"abs\s*\(\s*(\w+)\s*\)", expr, re.I)
        if abs_match:
            return table[abs_match.group(1)].abs()

        # Handle ROUND(col) or ROUND(col, decimals)
        round_match = re.match(r"round\s*\(\s*(\w+)(?:\s*,\s*(\d+))?\s*\)", expr, re.I)
        if round_match:
            col = table[round_match.group(1)]
            decimals = int(round_match.group(2)) if round_match.group(2) else 0
            return col.round(decimals)

        # Handle arithmetic expressions (e.g., "amount * 2", "price + tax")
        for op_str, op_func in [
            (" + ", lambda a, b: a + b),
            (" - ", lambda a, b: a - b),
            (" * ", lambda a, b: a * b),
            (" / ", lambda a, b: a / b),
        ]:
            if op_str in expr:
                parts = expr.split(op_str)
                if len(parts) == 2:
                    left = self._parse_operand(table, parts[0].strip())
                    right = self._parse_operand(table, parts[1].strip())
                    return op_func(left, right)

        # Check if it's just a column reference
        if expr in table.columns:
            return table[expr]

        # Try to parse as a literal value
        return ibis.literal(self._parse_value(expr))

    def _split_args(self, args_str: str) -> list[str]:
        """Split comma-separated arguments, handling nested parentheses."""
        args = []
        current = []
        depth = 0
        for char in args_str:
            if char == "(" :
                depth += 1
                current.append(char)
            elif char == ")":
                depth -= 1
                current.append(char)
            elif char == "," and depth == 0:
                args.append("".join(current).strip())
                current = []
            else:
                current.append(char)
        if current:
            args.append("".join(current).strip())
        return args

    def _parse_operand(self, table: ir.Table, operand: str) -> ibis.Expr:
        """Parse an operand (column or literal) into an Ibis expression."""
        operand = operand.strip()

        # Check if it's a column reference
        if operand in table.columns:
            return table[operand]

        # Otherwise, parse as a literal
        return ibis.literal(self._parse_value(operand))

    def derive_column(
        self,
        table: ir.Table,
        name: str,
        expr: str,
    ) -> ir.Table:
        """Add a computed column.

        Args:
            table: Input table
            name: New column name
            expr: SQL-like expression (e.g., "amount * 2")

        Returns:
            Table with new column
        """
        # Parse the expression into an Ibis expression
        ibis_expr = self._parse_expression(table, expr)
        return table.mutate(**{name: ibis_expr})

    def cast(self, table: ir.Table, columns: dict[str, str]) -> ir.Table:
        """Cast column types.

        Args:
            table: Input table
            columns: Column -> dtype mapping

        Returns:
            Table with cast columns
        """
        mutations = {}
        for col, dtype in columns.items():
            ibis_dtype = self._map_dtype(dtype)
            mutations[col] = table[col].cast(ibis_dtype)
        return table.mutate(**mutations)

    def _map_dtype(self, dtype: str) -> ibis.DataType:
        """Map string dtype to Ibis dtype."""
        dtype_map = {
            "string": ibis.dtype("string"),
            "str": ibis.dtype("string"),
            "int": ibis.dtype("int64"),
            "int32": ibis.dtype("int32"),
            "int64": ibis.dtype("int64"),
            "float": ibis.dtype("float64"),
            "float32": ibis.dtype("float32"),
            "float64": ibis.dtype("float64"),
            "bool": ibis.dtype("boolean"),
            "boolean": ibis.dtype("boolean"),
            "date": ibis.dtype("date"),
            "datetime": ibis.dtype("timestamp"),
            "timestamp": ibis.dtype("timestamp"),
        }
        if dtype.lower() in dtype_map:
            return dtype_map[dtype.lower()]
        # Try parsing as Ibis dtype directly
        return ibis.dtype(dtype)

    def fill_null(self, table: ir.Table, columns: dict[str, Any]) -> ir.Table:
        """Replace null values.

        Args:
            table: Input table
            columns: Column -> fill value mapping

        Returns:
            Table with nulls filled
        """
        mutations = {}
        for col, fill_value in columns.items():
            mutations[col] = table[col].fill_null(fill_value)
        return table.mutate(**mutations)

    def dedup(
        self,
        table: ir.Table,
        columns: list[str] | None = None,
    ) -> ir.Table:
        """Remove duplicate rows.

        Args:
            table: Input table
            columns: Columns to consider (None = all)

        Returns:
            Deduplicated table
        """
        if columns:
            return table.distinct(on=columns)
        return table.distinct()

    def sort(
        self,
        table: ir.Table,
        by: list[str],
        descending: bool = False,
    ) -> ir.Table:
        """Sort rows.

        Args:
            table: Input table
            by: Columns to sort by
            descending: Sort descending

        Returns:
            Sorted table
        """
        order_by = [ibis.desc(col) for col in by] if descending else by
        return table.order_by(order_by)

    def join(
        self,
        left: ir.Table,
        right: ir.Table,
        on: list[str],
        how: str = "inner",
    ) -> ir.Table:
        """Join two tables.

        Args:
            left: Left table
            right: Right table
            on: Join key columns
            how: Join type (inner, left, right, outer)

        Returns:
            Joined table
        """
        return left.join(right, predicates=on, how=how)

    def aggregate(
        self,
        table: ir.Table,
        group_by: list[str],
        aggs: dict[str, str],
    ) -> ir.Table:
        """Group and aggregate.

        Args:
            table: Input table
            group_by: Columns to group by
            aggs: Output column -> aggregation expression mapping
                  e.g., {"total": "sum(amount)", "count": "count(*)"}

        Returns:
            Aggregated table
        """
        # Parse aggregation expressions into Ibis expressions
        ibis_aggs = {}
        for name, expr in aggs.items():
            ibis_aggs[name] = self._parse_agg_expression(table, expr)

        return table.group_by(group_by).aggregate(**ibis_aggs)

    def _parse_agg_expression(self, table: ir.Table, expr: str) -> ibis.Expr:
        """Parse an aggregation expression like 'sum(amount)' into Ibis.

        Supported functions:
            - sum(column): Sum of values
            - avg(column), mean(column): Average of values
            - min(column): Minimum value
            - max(column): Maximum value
            - count(*), count(column): Count of rows/non-null values
            - count_distinct(column), nunique(column): Count of distinct values
            - first(column): First value
            - last(column): Last value
            - stddev(column), std(column): Standard deviation
            - variance(column), var(column): Variance
            - median(column): Median value
            - any(column): Any value (arbitrary)
            - collect(column): Collect values into array
        """
        import re

        # Pattern to match function(column) or function(*)
        match = re.match(r"(\w+)\s*\(\s*(\*|\w+)\s*\)", expr.strip())
        if not match:
            raise ValueError(f"Unable to parse aggregation expression: {expr}")

        func_name = match.group(1).lower()
        col_name = match.group(2)

        # Map function names to Ibis methods
        if col_name == "*":
            # count(*) is a special case
            if func_name == "count":
                return table.count()
            raise ValueError(f"Function {func_name}(*) not supported")

        col = table[col_name]
        match func_name:
            # Basic aggregations
            case "sum":
                return col.sum()
            case "avg" | "mean":
                return col.mean()
            case "min":
                return col.min()
            case "max":
                return col.max()
            case "count":
                return col.count()
            # Distinct count
            case "count_distinct" | "nunique":
                return col.nunique()
            # First/Last (NOTE: behavior may vary by backend)
            case "first":
                return col.first()
            case "last":
                return col.last()
            # Statistical functions
            case "stddev" | "std":
                return col.std()
            case "variance" | "var":
                return col.var()
            case "median":
                return col.median()
            # Other aggregations
            case "any" | "arbitrary":
                return col.arbitrary()
            case "collect" | "collect_list":
                return col.collect()
            case _:
                raise ValueError(f"Unknown aggregation function: {func_name}")

    def union(self, tables: list[ir.Table]) -> ir.Table:
        """Vertically concatenate tables.

        Args:
            tables: Tables to union

        Returns:
            Combined table
        """
        if not tables:
            raise ValueError("At least one table required for union")
        result = tables[0]
        for t in tables[1:]:
            result = result.union(t)
        return result

    def limit(self, table: ir.Table, n: int) -> ir.Table:
        """Limit to first N rows.

        Args:
            table: Input table
            n: Maximum rows

        Returns:
            Limited table
        """
        return table.limit(n)

    # =========================================================================
    # Transform Dispatch
    # =========================================================================

    def apply_transform(
        self,
        table: ir.Table,
        transform: TransformStep,
        context: dict[str, ir.Table] | None = None,
    ) -> ir.Table:
        """Apply a single transform step.

        Args:
            table: Input table
            transform: Transform configuration
            context: Optional dict of named tables for join/union operations

        Returns:
            Transformed table
        """
        match transform:
            case SelectTransform(columns=cols):
                return self.select(table, cols)
            case RenameTransform(mapping=mapping):
                return self.rename(table, mapping)
            case FilterTransform(predicate=pred):
                return self.filter(table, pred)
            case DeriveColumnTransform(name=name, expr=expr):
                return self.derive_column(table, name, expr)
            case CastTransform(columns=cols):
                return self.cast(table, cols)
            case FillNullTransform(columns=cols):
                return self.fill_null(table, cols)
            case DedupTransform(columns=cols):
                return self.dedup(table, cols)
            case SortTransform(by=by, descending=desc):
                return self.sort(table, by, desc)
            case AggregateTransform(group_by=gb, aggs=aggs):
                return self.aggregate(table, gb, aggs)
            case LimitTransform(n=n):
                return self.limit(table, n)
            case JoinTransform(right=right_name, on=on, how=how):
                if context is None or right_name not in context:
                    raise ValueError(
                        f"Join requires table '{right_name}' in context. "
                        f"Available: {list(context.keys()) if context else []}"
                    )
                right_table = context[right_name]
                return self.join(table, right_table, on, how)
            case UnionTransform(sources=source_names):
                if context is None:
                    raise ValueError("Union requires tables in context")
                # Start with current table, union with named sources
                tables = [table]
                for name in source_names:
                    if name not in context:
                        raise ValueError(
                            f"Union requires table '{name}' in context. "
                            f"Available: {list(context.keys())}"
                        )
                    tables.append(context[name])
                return self.union(tables)
            case _:
                raise NotImplementedError(f"Transform not implemented: {type(transform)}")

    def run_transforms(
        self,
        table: ir.Table,
        transforms: list[TransformStep],
        context: dict[str, ir.Table] | None = None,
    ) -> ir.Table:
        """Apply a sequence of transforms.

        Args:
            table: Input table
            transforms: List of transform configurations
            context: Optional dict of named tables for join/union operations

        Returns:
            Transformed table
        """
        for transform in transforms:
            table = self.apply_transform(table, transform, context)
        return table

    # =========================================================================
    # Output Conversions
    # =========================================================================

    def to_polars(self, table: ir.Table) -> pl.DataFrame:
        """Convert to Polars DataFrame.

        Args:
            table: Ibis Table expression

        Returns:
            Polars DataFrame
        """
        return self._con.to_polars(table)

    def to_pandas(self, table: ir.Table) -> pd.DataFrame:
        """Convert to pandas DataFrame.

        Args:
            table: Ibis Table expression

        Returns:
            pandas DataFrame
        """
        return self._con.to_pandas(table)

    def execute(self, table: ir.Table) -> Any:
        """Execute the expression and return results.

        Args:
            table: Ibis Table expression

        Returns:
            Materialized results (format depends on backend)
        """
        return table.execute()

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def row_count(self, table: ir.Table) -> int:
        """Get row count.

        Args:
            table: Ibis Table expression

        Returns:
            Number of rows
        """
        return table.count().execute()

    def columns(self, table: ir.Table) -> list[str]:
        """Get column names.

        Args:
            table: Ibis Table expression

        Returns:
            List of column names
        """
        return list(table.columns)

    def schema(self, table: ir.Table) -> dict[str, str]:
        """Get table schema.

        Args:
            table: Ibis Table expression

        Returns:
            Column name -> dtype mapping
        """
        return {name: str(dtype) for name, dtype in table.schema().items()}

    def compile(self, table: ir.Table) -> str:
        """Compile expression to SQL (for debugging).

        Args:
            table: Ibis Table expression

        Returns:
            SQL string (if backend supports it)
        """
        try:
            return str(ibis.to_sql(table))
        except Exception:
            return "<SQL compilation not supported for this backend>"
