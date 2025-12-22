"""Correlation ID and context utilities.

Provides correlation IDs for tracing requests across pipeline steps,
independent of OpenTelemetry.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

# Context variable to hold current correlation ID
_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str:
    """Get or generate a correlation ID for the current context.

    Returns:
        A unique correlation ID string.
    """
    current = _correlation_id.get()
    if current is None:
        current = str(uuid.uuid4())
        _correlation_id.set(current)
    return current


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context.

    Args:
        correlation_id: The correlation ID to set.
    """
    _correlation_id.set(correlation_id)


def reset_correlation_id() -> None:
    """Reset the correlation ID, generating a new one on next access."""
    _correlation_id.set(None)
