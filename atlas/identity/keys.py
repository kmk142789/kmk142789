"""Key rotation helpers using HKDF."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


@dataclass
class RotatingKeyManager:
    seed: bytes
    interval: timedelta = timedelta(hours=1)

    def derive(self, at: datetime | None = None) -> Tuple[bytes, datetime]:
        now = at or datetime.now(timezone.utc)
        epoch = int(now.timestamp() // self.interval.total_seconds())
        info = epoch.to_bytes(8, "big")
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info)
        key = hkdf.derive(self.seed)
        next_rotation = datetime.fromtimestamp((epoch + 1) * self.interval.total_seconds(), tz=timezone.utc)
        return key, next_rotation

    @classmethod
    def generate(cls) -> "RotatingKeyManager":
        return cls(seed=os.urandom(32))


__all__ = ["RotatingKeyManager"]
