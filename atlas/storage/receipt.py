"""Content-addressable storage receipts."""
from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from typing import Dict


@dataclass(slots=True)
class StorageReceipt:
    driver: str
    address: str
    digest: str
    size: int

    def to_dict(self) -> Dict[str, str | int]:
        return {
            "driver": self.driver,
            "address": self.address,
            "digest": self.digest,
            "size": self.size,
        }

    def verify(self, data: bytes) -> bool:
        digest = self.digest.split(":", 1)[0]
        return digest == compute_digest(data)


def compute_digest(data: bytes) -> str:
    sha = hashlib.sha256()
    sha.update(data)
    return base64.urlsafe_b64encode(sha.digest()).decode("ascii")


__all__ = ["StorageReceipt", "compute_digest"]
