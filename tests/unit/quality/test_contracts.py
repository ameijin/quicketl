"""Tests for the contracts module (schema, registry, pandera adapter)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import yaml

from quicketl.quality.contracts.schema import ColumnContract, DataContract

if TYPE_CHECKING:
    pass


# =============================================================================
# ColumnContract tests
# =============================================================================


class TestColumnContract:
    """Tests for ColumnContract model."""

    def test_minimal_column(self):
        col = ColumnContract(name="id", dtype="int64")
        assert col.name == "id"
        assert col.dtype == "int64"
        assert col.nullable is True
        assert col.unique is False
        assert col.checks == []

    def test_full_column(self):
        col = ColumnContract(
            name="amount",
            dtype="float64",
            nullable=False,
            unique=True,
            checks=["ge(0)", "le(10000)"],
            description="Order amount in USD",
        )
        assert col.nullable is False
        assert col.unique is True
        assert len(col.checks) == 2
        assert col.description == "Order amount in USD"


# =============================================================================
# DataContract tests
# =============================================================================


class TestDataContract:
    """Tests for DataContract model."""

    @pytest.fixture
    def sample_contract(self):
        return DataContract(
            name="orders",
            version="2.0.0",
            owner="data-team",
            description="Order transaction data",
            columns=[
                ColumnContract(name="order_id", dtype="int64", nullable=False, unique=True),
                ColumnContract(name="amount", dtype="float64", checks=["ge(0)"]),
                ColumnContract(name="status", dtype="str"),
            ],
        )

    def test_contract_fields(self, sample_contract):
        assert sample_contract.name == "orders"
        assert sample_contract.version == "2.0.0"
        assert sample_contract.owner == "data-team"
        assert len(sample_contract.columns) == 3

    def test_column_names(self, sample_contract):
        assert sample_contract.column_names() == ["order_id", "amount", "status"]

    def test_required_columns(self, sample_contract):
        assert sample_contract.required_columns() == ["order_id"]

    def test_unique_columns(self, sample_contract):
        assert sample_contract.unique_columns() == ["order_id"]

    def test_get_column_found(self, sample_contract):
        col = sample_contract.get_column("amount")
        assert col is not None
        assert col.dtype == "float64"

    def test_get_column_not_found(self, sample_contract):
        assert sample_contract.get_column("nonexistent") is None

    def test_to_pandera_config(self, sample_contract):
        config = sample_contract.to_pandera_config()
        assert config["name"] == "orders"
        assert config["strict"] is False
        assert "order_id" in config["columns"]
        assert config["columns"]["order_id"]["nullable"] is False
        assert config["columns"]["order_id"]["unique"] is True
        assert config["columns"]["amount"]["checks"] == ["ge(0)"]

    def test_default_version(self):
        contract = DataContract(
            name="test",
            columns=[ColumnContract(name="id", dtype="int64")],
        )
        assert contract.version == "1.0.0"

    def test_strict_mode(self):
        contract = DataContract(
            name="strict_test",
            columns=[ColumnContract(name="id", dtype="int64")],
            strict=True,
        )
        config = contract.to_pandera_config()
        assert config["strict"] is True


# =============================================================================
# ContractRegistry tests
# =============================================================================


class TestContractRegistry:
    """Tests for ContractRegistry."""

    @pytest.fixture
    def contracts_dir(self, tmp_path):
        """Create a temp directory with contract YAML files."""
        orders = {
            "name": "orders",
            "version": "1.0.0",
            "columns": [
                {"name": "id", "dtype": "int64", "nullable": False, "unique": True},
                {"name": "amount", "dtype": "float64"},
            ],
        }
        customers = {
            "name": "customers",
            "version": "2.0.0",
            "columns": [
                {"name": "customer_id", "dtype": "int64"},
                {"name": "email", "dtype": "str"},
            ],
        }

        (tmp_path / "orders.yml").write_text(yaml.dump(orders))
        (tmp_path / "customers.yaml").write_text(yaml.dump(customers))
        return tmp_path

    def test_list_contracts(self, contracts_dir):
        from quicketl.quality.contracts.registry import ContractRegistry

        registry = ContractRegistry(contracts_dir)
        names = registry.list_contracts()
        assert sorted(names) == ["customers", "orders"]

    def test_get_contract_yml(self, contracts_dir):
        from quicketl.quality.contracts.registry import ContractRegistry

        registry = ContractRegistry(contracts_dir)
        contract = registry.get_contract("orders")
        assert contract.name == "orders"
        assert contract.version == "1.0.0"
        assert len(contract.columns) == 2

    def test_get_contract_yaml(self, contracts_dir):
        from quicketl.quality.contracts.registry import ContractRegistry

        registry = ContractRegistry(contracts_dir)
        contract = registry.get_contract("customers")
        assert contract.name == "customers"

    def test_get_contract_not_found(self, contracts_dir):
        from quicketl.quality.contracts.registry import ContractRegistry

        registry = ContractRegistry(contracts_dir)
        with pytest.raises(FileNotFoundError, match="Contract not found"):
            registry.get_contract("nonexistent")

    def test_has_contract(self, contracts_dir):
        from quicketl.quality.contracts.registry import ContractRegistry

        registry = ContractRegistry(contracts_dir)
        assert registry.has_contract("orders") is True
        assert registry.has_contract("nonexistent") is False

    def test_get_contract_path(self, contracts_dir):
        from quicketl.quality.contracts.registry import ContractRegistry

        registry = ContractRegistry(contracts_dir)
        path = registry.get_contract_path("orders")
        assert path is not None
        assert path.name == "orders.yml"

        assert registry.get_contract_path("nonexistent") is None

    def test_validate_all(self, contracts_dir):
        from quicketl.quality.contracts.registry import ContractRegistry

        registry = ContractRegistry(contracts_dir)
        results = registry.validate_all()
        assert results == {"customers": True, "orders": True}

    def test_validate_all_with_invalid(self, contracts_dir):
        from quicketl.quality.contracts.registry import ContractRegistry

        # Write invalid YAML contract
        (contracts_dir / "broken.yml").write_text("name: broken\n")
        registry = ContractRegistry(contracts_dir)
        results = registry.validate_all()
        assert results["orders"] is True
        assert results["broken"] is False

    def test_nonexistent_directory(self):
        from quicketl.quality.contracts.registry import ContractRegistry

        with pytest.raises(FileNotFoundError):
            ContractRegistry(Path("/nonexistent/path"))

    def test_file_not_directory(self, tmp_path):
        from quicketl.quality.contracts.registry import ContractRegistry

        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("content")
        with pytest.raises(NotADirectoryError):
            ContractRegistry(file_path)


# =============================================================================
# PanderaContractValidator tests (skip if pandera not installed)
# =============================================================================

try:
    import pandera  # noqa: F401
    _has_pandera = True
except ImportError:
    _has_pandera = False


@pytest.mark.skipif(not _has_pandera, reason="pandera not installed")
class TestPanderaContractValidator:
    """Tests for PanderaContractValidator (requires pandera)."""

    @pytest.fixture
    def sample_table(self):
        from quicketl.engines import QuickETLEngine

        engine = QuickETLEngine(backend="duckdb")
        import pandas as pd

        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "amount": [100.0, 200.0, 150.0],
        })
        return engine.connection.create_table("contract_test", df, overwrite=True)

    def test_valid_data_passes(self, sample_table):
        from quicketl.quality.contracts.pandera_adapter import PanderaContractValidator

        validator = PanderaContractValidator({
            "columns": {
                "id": {"dtype": "int64", "nullable": False},
                "name": {"dtype": "str"},
                "amount": {"dtype": "float64", "checks": ["ge(0)"]},
            },
        })
        result = validator.validate(sample_table)
        assert result.passed is True
        assert result.validated_rows == 3

    def test_invalid_data_fails(self, sample_table):
        from quicketl.quality.contracts.pandera_adapter import PanderaContractValidator

        validator = PanderaContractValidator({
            "columns": {
                "amount": {"dtype": "float64", "checks": ["ge(500)"]},
            },
        })
        result = validator.validate(sample_table)
        assert result.passed is False
        assert len(result.errors) > 0

    def test_schema_name(self, sample_table):
        from quicketl.quality.contracts.pandera_adapter import PanderaContractValidator

        validator = PanderaContractValidator({
            "name": "test_schema",
            "columns": {
                "id": {"dtype": "int64"},
            },
        })
        result = validator.validate(sample_table)
        assert result.schema_name == "test_schema"

    def test_run_contract_check(self, sample_table):
        """Test the run_contract_check integration in quality/checks.py."""
        from quicketl.config.checks import ContractCheck
        from quicketl.quality.checks import run_contract_check

        config = ContractCheck(
            contract_schema={
                "columns": {
                    "id": {"dtype": "int64", "nullable": False},
                    "amount": {"dtype": "float64", "checks": ["ge(0)"]},
                },
            },
        )
        result = run_contract_check(sample_table, config)
        assert result.passed is True
        assert result.check_type == "contract"
