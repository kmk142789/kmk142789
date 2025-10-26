"""Simple append-only ledger for deposits and payouts."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List


@dataclass
class LedgerEntry:
    """Represents a single movement of funds through the digital bank."""

    type: str
    amount_wei: int
    tx_hash: str
    actor: str
    timestamp: int


class Ledger:
    """Maintains a JSON-serialized ledger that mirrors on-chain events."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: List[LedgerEntry] = []
        if path.exists():
            self._load()

    def _load(self) -> None:
        raw_entries = json.loads(self._path.read_text())
        self._entries = [LedgerEntry(**entry) for entry in raw_entries]

    def append(self, entry: LedgerEntry) -> None:
        self._entries.append(entry)
        self._path.write_text(json.dumps([asdict(e) for e in self._entries], indent=2))

    def entries(self) -> Iterable[LedgerEntry]:
        return tuple(self._entries)

    def total_deposits(self) -> int:
        return sum(entry.amount_wei for entry in self._entries if entry.type == "deposit")

    def total_payouts(self) -> int:
        return sum(entry.amount_wei for entry in self._entries if entry.type == "payout")

    def balance(self) -> int:
        return self.total_deposits() - self.total_payouts()
