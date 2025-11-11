"""Vault v1 adapter driver."""
from __future__ import annotations

import base64
import hmac
import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Optional

from ..receipt import StorageReceipt, compute_digest


@dataclass
class VaultV1Driver:
    base_path: Path
    signing_key: bytes
    name: str = "vault_v1"

    def __post_init__(self) -> None:
        self.base_path.mkdir(parents=True, exist_ok=True)

    def put(self, path: str, data: bytes) -> StorageReceipt:
        digest = compute_digest(data)
        location = self.base_path / digest
        location.parent.mkdir(parents=True, exist_ok=True)
        location.write_bytes(data)
        signature = self._sign_receipt(path, digest, len(data))
        receipt = StorageReceipt(self.name, path, f"{digest}:{signature}", len(data))
        return receipt

    def get(self, path: str) -> bytes:
        digest, _ = self._split_digest(path)
        data = (self.base_path / digest).read_bytes()
        return data

    def delete(self, path: str) -> None:
        digest, _ = self._split_digest(path)
        target = self.base_path / digest
        if target.exists():
            target.unlink()

    def verify(self, receipt: StorageReceipt, data: bytes) -> bool:
        digest, signature = self._split_digest(receipt.digest)
        if digest != compute_digest(data):
            return False
        expected = self._sign_receipt(receipt.address, digest, receipt.size)
        return hmac.compare_digest(signature, expected)

    def _sign_receipt(self, address: str, digest: str, size: int) -> str:
        payload = json.dumps({"address": address, "digest": digest, "size": size}, sort_keys=True).encode()
        mac = hmac.new(self.signing_key, payload, sha256).digest()
        return base64.urlsafe_b64encode(mac).decode("ascii")

    def _split_digest(self, digest_field: str) -> tuple[str, str]:
        if ":" not in digest_field:
            raise ValueError("Invalid receipt digest")
        digest, signature = digest_field.split(":", 1)
        return digest, signature


__all__ = ["VaultV1Driver"]
