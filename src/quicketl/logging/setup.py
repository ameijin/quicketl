"""Logging configuration using structlog.

Provides JSON output for production and pretty console output for development.
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Literal

import structlog

if TYPE_CHECKING:
    from structlog.stdlib import BoundLogger


def configure_logging(
    level: str = "INFO",
    format: Literal["json", "console", "auto"] = "auto",
) -> None:
    """Configure structlog for ETLX.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Output format
            - 'json': Machine-readable JSON output (production)
            - 'console': Pretty colored output (development)
            - 'auto': JSON if not a TTY, console if TTY

    Example:
        >>> from quicketl.logging import configure_logging, get_logger
        >>> configure_logging(level="DEBUG", format="console")
        >>> log = get_logger()
        >>> log.info("pipeline_started", name="my_pipeline")
    """
    # Determine actual format based on auto-detection
    actual_format = ("console" if sys.stderr.isatty() else "json") if format == "auto" else format

    # Shared processors for all formats
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if actual_format == "json":
        # Production: JSON output
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(sort_keys=True),
        ]
    else:
        # Development: Pretty console output with colors
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=getattr(logging, level.upper()),
    )


def get_logger(name: str | None = None) -> BoundLogger:
    """Get a configured structlog logger.

    Args:
        name: Logger name (typically __name__)

    Returns:
        A bound structlog logger

    Example:
        >>> log = get_logger(__name__)
        >>> log.info("processing", rows=1000)
    """
    return structlog.get_logger(name)


# Auto-configure with defaults on import
configure_logging()
