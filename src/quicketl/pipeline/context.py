"""Pipeline execution context.

Provides runtime context for pipeline execution including variables,
metadata, and cross-step state.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import ibis.expr.types as ir


@dataclass
class ExecutionContext:
    """Runtime context for pipeline execution.

    Stores variables, intermediate results, and execution metadata.

    Attributes:
        variables: Key-value pairs for variable substitution
        tables: Named intermediate table results
        metadata: Execution metadata (timestamps, run_id, etc.)
        start_time: When execution started
    """

    variables: dict[str, str] = field(default_factory=dict)
    tables: dict[str, ir.Table] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Initialize default metadata."""
        if "run_id" not in self.metadata:
            self.metadata["run_id"] = self.start_time.strftime("%Y%m%d_%H%M%S")

    @classmethod
    def from_env(cls, prefix: str = "ETLX_") -> ExecutionContext:
        """Create context with variables from environment.

        Args:
            prefix: Environment variable prefix to filter

        Returns:
            ExecutionContext with environment variables

        Examples:
            >>> # With ETLX_DATABASE_URL set in environment
            >>> ctx = ExecutionContext.from_env()
            >>> ctx.variables["DATABASE_URL"]
        """
        variables = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Strip prefix for variable name
                var_name = key[len(prefix) :]
                variables[var_name] = value
        return cls(variables=variables)

    def get_variable(self, name: str, default: str | None = None) -> str | None:
        """Get a variable value.

        Args:
            name: Variable name
            default: Default value if not found

        Returns:
            Variable value or default
        """
        return self.variables.get(name, default)

    def set_variable(self, name: str, value: str) -> None:
        """Set a variable value.

        Args:
            name: Variable name
            value: Variable value
        """
        self.variables[name] = value

    def store_table(self, name: str, table: ir.Table) -> None:
        """Store an intermediate table result.

        Args:
            name: Table name for later reference
            table: Ibis Table expression
        """
        self.tables[name] = table

    def get_table(self, name: str) -> ir.Table:
        """Retrieve a stored table.

        Args:
            name: Table name

        Returns:
            Stored Ibis Table expression

        Raises:
            KeyError: If table not found
        """
        if name not in self.tables:
            raise KeyError(f"Table '{name}' not found in context. Available: {list(self.tables.keys())}")
        return self.tables[name]

    def has_table(self, name: str) -> bool:
        """Check if a table exists in context.

        Args:
            name: Table name

        Returns:
            True if table exists
        """
        return name in self.tables

    @property
    def elapsed_seconds(self) -> float:
        """Seconds elapsed since execution started."""
        delta = datetime.now(timezone.utc) - self.start_time
        return delta.total_seconds()

    @property
    def run_id(self) -> str:
        """Unique identifier for this execution run."""
        return self.metadata["run_id"]

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary (for logging/serialization).

        Returns:
            Dict representation (excludes tables which aren't serializable)
        """
        return {
            "variables": self.variables,
            "metadata": self.metadata,
            "start_time": self.start_time.isoformat(),
            "stored_tables": list(self.tables.keys()),
        }
