"""Retry logic with exponential backoff for cloud I/O operations."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

_CLOUD_PREFIXES = ("s3://", "gs://", "gcs://", "az://", "abfss://", "abfs://")

# Default retry settings
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0
DEFAULT_MAX_DELAY = 30.0

# Exceptions that indicate transient cloud I/O failures
RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    OSError,
    IOError,
    ConnectionError,
    TimeoutError,
)


def is_cloud_path(path: str) -> bool:
    """Check if a path is a cloud storage URI.

    Args:
        path: File path to check.

    Returns:
        True if the path starts with a known cloud prefix.
    """
    return path.startswith(_CLOUD_PREFIXES)


def with_retry(
    fn: Callable[..., T],
    *args: Any,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    retryable_exceptions: tuple[type[Exception], ...] = RETRYABLE_EXCEPTIONS,
    **kwargs: Any,
) -> T:
    """Execute a function with exponential backoff retry.

    Only retries on transient exceptions. Non-retryable errors propagate
    immediately.

    Args:
        fn: Function to execute.
        *args: Positional arguments for fn.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds between retries.
        max_delay: Maximum delay in seconds between retries.
        retryable_exceptions: Exception types that trigger retry.
        **kwargs: Keyword arguments for fn.

    Returns:
        The return value of fn.

    Raises:
        The last exception if all retries are exhausted.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except retryable_exceptions as exc:
            last_exception = exc
            if attempt == max_retries:
                break
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(
                "Retry %d/%d after %.1fs: %s",
                attempt + 1,
                max_retries,
                delay,
                exc,
            )
            time.sleep(delay)

    raise last_exception  # type: ignore[misc]
