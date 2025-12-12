"""ETLX data writers."""

from quicketl.io.writers.file import write_file
from quicketl.io.writers.database import write_database

__all__ = ["write_file", "write_database"]
