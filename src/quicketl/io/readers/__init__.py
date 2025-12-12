"""ETLX data readers."""

from quicketl.io.readers.file import read_file
from quicketl.io.readers.database import read_database

__all__ = ["read_file", "read_database"]
