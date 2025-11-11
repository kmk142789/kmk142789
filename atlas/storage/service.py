"""Storage service orchestrating drivers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from atlas.core.logging import get_logger

from .drivers.base import StorageDriver
from .drivers.fs import FileSystemDriver
from .drivers.memory import MemoryStorageDriver
from .drivers.vault import VaultV1Driver
from .receipt import StorageReceipt, compute_digest


@dataclass
class StorageService:
    config: Dict[str, str | int | float | bool]
    base_path: Path
    drivers: Dict[str, StorageDriver] | None = None

    def __post_init__(self) -> None:
        self.logger = get_logger("atlas.storage")
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.drivers = self.drivers or self._build_default_drivers()

    def _build_default_drivers(self) -> Dict[str, StorageDriver]:
        signing_key = str(self.config.get("vault_signing_key", "atlas-secret")).encode()
        return {
            "memory": MemoryStorageDriver(),
            "fs": FileSystemDriver(self.base_path / "fs"),
            "vault_v1": VaultV1Driver(self.base_path / "vault", signing_key),
        }

    def put(self, driver_name: str, path: str, data: bytes) -> StorageReceipt:
        driver = self._driver(driver_name)
        receipt = driver.put(path, data)
        if driver_name != "vault_v1":
            # Ensure content addressable receipts
            receipt.digest = compute_digest(data)
        self.logger.info("storage_put", extra={"ctx_driver": driver_name, "ctx_path": path})
        return receipt

    def get(self, driver_name: str, receipt: StorageReceipt) -> bytes:
        driver = self._driver(driver_name)
        data = driver.get(receipt.address if driver_name != "vault_v1" else receipt.digest)
        if hasattr(driver, "verify"):
            if not driver.verify(receipt, data):  # type: ignore[attr-defined]
                raise ValueError("Receipt verification failed")
        elif not receipt.verify(data):
            raise ValueError("Receipt verification failed")
        return data

    def delete(self, driver_name: str, receipt: StorageReceipt) -> None:
        driver = self._driver(driver_name)
        driver.delete(receipt.address if driver_name != "vault_v1" else receipt.digest)

    def _driver(self, name: str) -> StorageDriver:
        if not self.drivers or name not in self.drivers:
            raise KeyError(f"Driver {name} not available")
        return self.drivers[name]


__all__ = ["StorageService"]
