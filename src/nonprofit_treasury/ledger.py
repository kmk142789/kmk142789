"""Append-only ledger for NonprofitTreasury events."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Literal, Optional


EntryType = Literal["donation", "disbursement"]


@dataclass
class TreasuryLedgerEntry:
    """Represents an event captured from the NonprofitTreasury contract."""

    type: EntryType
    amount: int
    token_address: str
    tx_hash: str
    actor: str
    timestamp: int
    memo: Optional[str] = None
    reason: Optional[str] = None


class TreasuryLedger:
    """Maintains a JSON ledger mirroring the on-chain donation and disbursement feed."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: List[TreasuryLedgerEntry] = []
        if path.exists():
            self._load()

    def _load(self) -> None:
        raw_entries = json.loads(self._path.read_text())
        self._entries = [TreasuryLedgerEntry(**entry) for entry in raw_entries]

    def append(self, entry: TreasuryLedgerEntry) -> None:
        self._entries.append(entry)
        self._path.write_text(json.dumps([asdict(e) for e in self._entries], indent=2))

    def entries(self) -> Iterable[TreasuryLedgerEntry]:
        return tuple(self._entries)

    def total_donations(self) -> int:
        return sum(entry.amount for entry in self._entries if entry.type == "donation")

    def total_disbursed(self) -> int:
        return sum(entry.amount for entry in self._entries if entry.type == "disbursement")

    def balance(self) -> int:
        return self.total_donations() - self.total_disbursed()
