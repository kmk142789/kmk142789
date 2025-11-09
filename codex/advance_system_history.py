"""Recursive self-fork tracking utilities."""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterator, Mapping, MutableMapping

__all__ = [
    "DEFAULT_ADVANCE_PATH",
    "ForkRecord",
    "RecursiveForkTracker",
]

DEFAULT_ADVANCE_PATH = Path(
    os.environ.get("ECHO_ADVANCE_HISTORY_PATH", "genesis_ledger/advance_history.jsonl")
)


@dataclass(slots=True)
class ForkRecord:
    """Single fork lineage entry."""

    fork_id: str
    platform: str
    summary: str
    timestamp: float
    proposal: Mapping[str, object]

    def to_json(self) -> str:
        payload = asdict(self)
        payload["timestamp"] = round(self.timestamp, 6)
        return json.dumps(payload, ensure_ascii=False)


class RecursiveForkTracker:
    """Append-only tracker for recursive forks and proposals."""

    def __init__(self, history_path: Path | str | None = None, *, cache_limit: int = 512) -> None:
        self.history_path = Path(history_path or DEFAULT_ADVANCE_PATH)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_limit = cache_limit
        self._cache: list[ForkRecord] | None = None

    def _append(self, record: ForkRecord) -> None:
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(record.to_json() + "\n")
        if self._cache is not None:
            self._cache.append(record)
            if len(self._cache) > self.cache_limit:
                self._cache = self._cache[-self.cache_limit :]

    def iter_history(self) -> Iterator[ForkRecord]:
        if self._cache is None:
            records: list[ForkRecord] = []
            if self.history_path.exists():
                with self.history_path.open("r", encoding="utf-8") as handle:
                    for raw in handle:
                        try:
                            payload = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        if not isinstance(payload, MutableMapping):
                            continue
                        records.append(
                            ForkRecord(
                                fork_id=str(payload.get("fork_id", "")),
                                platform=str(payload.get("platform", "")),
                                summary=str(payload.get("summary", "")),
                                timestamp=float(payload.get("timestamp", 0.0)),
                                proposal=dict(payload.get("proposal", {})),
                            )
                        )
            self._cache = records
        yield from self._cache

    def record_fork(
        self,
        fork_id: str,
        *,
        platform: str,
        summary: str,
        proposal: Mapping[str, object] | None = None,
    ) -> ForkRecord:
        """Record a fork event."""

        if not fork_id:
            raise ValueError("fork_id must be provided")
        if not platform:
            raise ValueError("platform must be provided")
        record = ForkRecord(
            fork_id=fork_id,
            platform=platform,
            summary=summary,
            timestamp=time.time(),
            proposal=dict(proposal or {}),
        )
        self._append(record)
        return record

    def fork_propose_upgrade(self, pr_title: str, summary: str) -> ForkRecord:
        """Create a fork proposal entry referencing ``pr_title``."""

        if not pr_title:
            raise ValueError("pr_title must not be empty")
        if not summary:
            raise ValueError("summary must not be empty")
        proposal_payload = {
            "title": pr_title,
            "summary": summary,
            "hash": sha256(f"{pr_title}|{summary}".encode("utf-8")).hexdigest(),
        }
        fork_id = proposal_payload["hash"][:12]
        record = ForkRecord(
            fork_id=fork_id,
            platform="codex",
            summary=summary,
            timestamp=time.time(),
            proposal=proposal_payload,
        )
        self._append(record)
        return record

    def snapshot(self, limit: int | None = None) -> list[Mapping[str, object]]:
        """Return a serialisable snapshot of the most recent entries."""

        records = list(self.iter_history())
        if limit is not None and limit >= 0:
            records = records[-limit:]
        return [asdict(record) for record in records]
