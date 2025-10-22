"""Pulse history streaming and attestation helpers."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, Iterable, List, Mapping, Sequence

from echo.atlas.temporal_ledger import LedgerEntry, LedgerEntryInput, TemporalLedger

from tools.pulse_daily_activity import DailyActivitySummary, calculate_daily_activity

from .models import PulseHistoryEntry


class PulseHistoryStreamer:
    """Tail ``pulse_history.json`` and emit entries as they arrive."""

    def __init__(
        self,
        history_path: Path | str,
        *,
        poll_interval: float = 1.0,
    ) -> None:
        self._history_path = Path(history_path)
        self._poll_interval = max(0.1, float(poll_interval))
        self._seen_hashes: set[str] = set()

    def load_entries(self) -> List[PulseHistoryEntry]:
        """Return all entries currently stored in the history file."""

        if not self._history_path.exists():
            return []
        data = json.loads(self._history_path.read_text(encoding="utf-8"))
        entries: List[PulseHistoryEntry] = []
        for item in data:
            try:
                timestamp = float(item["timestamp"])
                message = str(item.get("message", ""))
                digest = str(item.get("hash") or "")
            except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - defensive
                raise ValueError("pulse history entry missing required fields") from exc
            entries.append(PulseHistoryEntry(timestamp=timestamp, message=message, hash=digest))
        return entries

    def mark_seen(self, entries: Iterable[PulseHistoryEntry]) -> None:
        for entry in entries:
            self._seen_hashes.add(entry.hash)

    def daily_summary(self) -> DailyActivitySummary:
        entries = [
            {"timestamp": entry.timestamp, "message": entry.message, "hash": entry.hash}
            for entry in self.load_entries()
        ]
        if not entries:
            return DailyActivitySummary(
                total_days=0,
                total_entries=0,
                busiest_day=None,
                quietest_day=None,
                activity=(),
            )
        return calculate_daily_activity(entries, tz=timezone.utc)

    async def subscribe(self) -> AsyncIterator[PulseHistoryEntry]:
        """Yield new pulse entries as they appear on disk."""

        while True:
            for entry in self._collect_new_entries():
                yield entry
            await asyncio.sleep(self._poll_interval)

    def _collect_new_entries(self) -> Sequence[PulseHistoryEntry]:
        fresh: List[PulseHistoryEntry] = []
        for entry in self.load_entries():
            if entry.hash and entry.hash not in self._seen_hashes:
                self._seen_hashes.add(entry.hash)
                fresh.append(entry)
        return fresh


class PulseAttestor:
    """Append temporal ledger entries for pulse events."""

    def __init__(self, ledger: TemporalLedger, *, actor: str = "PulseNet Gateway") -> None:
        self._ledger = ledger
        self._actor = actor
        existing = ledger.entries()
        self._known: dict[str, LedgerEntry] = {entry.proof_id: entry for entry in existing}

    def ensure(self, entries: Iterable[PulseHistoryEntry]) -> List[Mapping[str, object]]:
        records: List[Mapping[str, object]] = []
        for entry in entries:
            records.append(self.attest(entry))
        return records

    def attest(self, entry: PulseHistoryEntry) -> Mapping[str, object]:
        if entry.hash in self._known:
            return self._serialise(self._known[entry.hash])
        ledger_entry = self._ledger.append(
            LedgerEntryInput(
                actor=self._actor,
                action="pulse-recorded",
                ref=entry.message,
                proof_id=entry.hash or entry.message,
                ts=datetime.fromtimestamp(entry.timestamp, tz=timezone.utc),
            )
        )
        self._known[entry.hash] = ledger_entry
        return self._serialise(ledger_entry)

    def latest(self, *, limit: int = 10) -> List[Mapping[str, object]]:
        entries = self._ledger.entries()
        if limit > 0:
            entries = entries[-limit:]
        return [self._serialise(item) for item in reversed(entries)]

    @staticmethod
    def _serialise(entry: LedgerEntry) -> Mapping[str, object]:
        return {
            "id": entry.id,
            "ts": entry.ts.isoformat(),
            "actor": entry.actor,
            "action": entry.action,
            "ref": entry.ref,
            "proof_id": entry.proof_id,
            "hash": entry.hash,
        }


__all__ = ["PulseAttestor", "PulseHistoryStreamer"]
