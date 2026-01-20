"""Data contracts and schema validation for QuickETL.

Provides Pandera-based schema validation for data quality contracts.
"""

from quicketl.quality.contracts.pandera_adapter import (
    ContractResult,
    PanderaContractValidator,
)
from quicketl.quality.contracts.registry import ContractRegistry
from quicketl.quality.contracts.schema import ColumnContract, DataContract

__all__ = [
    "ContractResult",
    "PanderaContractValidator",
    "ContractRegistry",
    "ColumnContract",
    "DataContract",
]
