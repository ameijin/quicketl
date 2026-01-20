"""File-based contract registry.

Provides a simple file-based registry for loading and managing
data contracts stored as YAML files.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from quicketl.quality.contracts.schema import DataContract


class ContractRegistry:
    """Load and manage data contracts from YAML files.

    Contracts are stored as YAML files in a directory structure.
    The registry supports loading contracts by name and listing
    all available contracts.

    Directory structure:
        contracts/
            orders_v1.yml
            customers_v2.yml
            products.yml

    Example:
        >>> registry = ContractRegistry(Path("./contracts"))
        >>> contract = registry.get_contract("orders_v1")
        >>> print(contract.version)
        '1.0.0'

        >>> # List all contracts
        >>> for name in registry.list_contracts():
        ...     print(name)

        >>> # Validate all contracts are parseable
        >>> results = registry.validate_all()
        >>> print(results)
        {'orders_v1': True, 'customers_v2': True}
    """

    def __init__(self, contracts_dir: Path | str):
        """Initialize registry with contracts directory.

        Args:
            contracts_dir: Path to directory containing contract YAML files.

        Raises:
            FileNotFoundError: If directory does not exist.
        """
        self.contracts_dir = Path(contracts_dir)
        if not self.contracts_dir.exists():
            raise FileNotFoundError(f"Contracts directory not found: {contracts_dir}")
        if not self.contracts_dir.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {contracts_dir}")

    def list_contracts(self) -> list[str]:
        """List all available contract names.

        Returns:
            Sorted list of contract names (filenames without extension).
        """
        contracts = set()
        for ext in [".yml", ".yaml"]:
            for file in self.contracts_dir.glob(f"*{ext}"):
                contracts.add(file.stem)
        return sorted(contracts)

    def get_contract(self, name: str, _version: str | None = None) -> DataContract:
        """Load contract by name.

        Args:
            name: Contract name (filename without extension).
            version: Optional version filter (not yet implemented - returns latest).

        Returns:
            DataContract object.

        Raises:
            FileNotFoundError: If contract file not found.
            ValueError: If contract file is invalid.
        """
        # Try .yml first, then .yaml
        for ext in [".yml", ".yaml"]:
            path = self.contracts_dir / f"{name}{ext}"
            if path.exists():
                return self._load_contract(path)

        raise FileNotFoundError(f"Contract not found: {name}")

    def _load_contract(self, path: Path) -> DataContract:
        """Load contract from YAML file.

        Args:
            path: Path to contract YAML file.

        Returns:
            DataContract object.

        Raises:
            ValueError: If YAML is invalid or missing required fields.
        """
        try:
            with path.open() as f:
                data = yaml.safe_load(f)

            if data is None:
                raise ValueError(f"Empty contract file: {path}")

            return DataContract(**data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {path}: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to load contract from {path}: {e}") from e

    def validate_all(self) -> dict[str, bool]:
        """Validate all contract files are parseable.

        Returns:
            Dict mapping contract names to validation status.
        """
        results = {}
        for name in self.list_contracts():
            try:
                self.get_contract(name)
                results[name] = True
            except Exception:
                results[name] = False
        return results

    def has_contract(self, name: str) -> bool:
        """Check if a contract exists.

        Args:
            name: Contract name to check.

        Returns:
            True if contract exists, False otherwise.
        """
        for ext in [".yml", ".yaml"]:
            path = self.contracts_dir / f"{name}{ext}"
            if path.exists():
                return True
        return False

    def get_contract_path(self, name: str) -> Path | None:
        """Get the file path for a contract.

        Args:
            name: Contract name.

        Returns:
            Path to contract file, or None if not found.
        """
        for ext in [".yml", ".yaml"]:
            path = self.contracts_dir / f"{name}{ext}"
            if path.exists():
                return path
        return None
