"""Abstract base class for vector store sinks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AbstractVectorSink(ABC):
    """Abstract base class for vector store sinks.

    Subclasses must implement the write method to store vectors.
    """

    @abstractmethod
    def write(self, data: list[dict[str, Any]]) -> None:
        """Write vectors to the store.

        Args:
            data: List of dicts containing id, vector, and optional metadata.
        """
        ...
