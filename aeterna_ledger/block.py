"""Block definitions for the Aeterna Ledger demo."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import List


@dataclass
class Block:
    """A single block in the Aeterna Ledger."""

    index: int
    memories: List[str]
    timestamp: float
    previous_hash: str
    nonce: int = 0
    hash: str | None = field(default=None)

    def compute_hash(self) -> str:
        """Compute a deterministic hash for the block contents."""

        block_dict = {
            "index": self.index,
            "memories": self.memories,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }
        block_string = json.dumps(block_dict, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self) -> dict:
        """Return a serializable representation of the block."""

        return {
            "index": self.index,
            "memories": self.memories,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
        }
