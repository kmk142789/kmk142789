"""High level service for the Pulse Weaver ledger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

from .adapters.sqlite import SQLiteAdapter
from .core import PulseWeaverSnapshot, WeaveFragment
from .schema import get_validator
from .storage.migrations import apply_migrations
from .storage.repository import PulseWeaverRepository


@dataclass(slots=True)
class _Counts:
    total: int
    by_status: Dict[str, int]
    atlas: Dict[str, int]
    phantom: Dict[str, int]


class PulseWeaverService:
    """Coordinate storage, phantom traces, and summaries."""

    SNAPSHOT_SCHEMA = "pulse.weaver/snapshot-v1"

    def __init__(
        self,
        project_root: Path,
        *,
        adapter: Optional[SQLiteAdapter] = None,
        phantom_history: Optional[Path] = None,
    ) -> None:
        self.project_root = project_root
        db_path = project_root / "data" / "pulse_weaver.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.adapter = adapter or SQLiteAdapter(db_path)
        self.repository = PulseWeaverRepository(self.adapter)
        self._validator = get_validator()
        self._phantom_history = phantom_history or (project_root / "pulse_history.json")
        self._ready = False

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def ensure_ready(self) -> None:
        if self._ready:
            return
        apply_migrations(self.adapter)
        self._ready = True

    # ------------------------------------------------------------------
    # Recording events
    # ------------------------------------------------------------------
    def record_failure(
        self,
        *,
        key: str,
        message: str,
        proof: str | None = None,
        echo: str | None = None,
        cycle: str | None = None,
        metadata: Optional[Mapping[str, object]] = None,
        atlas_node: str | None = None,
        phantom_trace: str | None = None,
    ) -> WeaveFragment:
        return self._record_event(
            key=key,
            message=message,
            status="failure",
            proof=proof,
            echo=echo,
            cycle=cycle,
            metadata=metadata,
            atlas_node=atlas_node,
            phantom_trace=phantom_trace,
        )

    def record_success(
        self,
        *,
        key: str,
        message: str,
        proof: str | None = None,
        echo: str | None = None,
        cycle: str | None = None,
        metadata: Optional[Mapping[str, object]] = None,
        atlas_node: str | None = None,
        phantom_trace: str | None = None,
    ) -> WeaveFragment:
        return self._record_event(
            key=key,
            message=message,
            status="success",
            proof=proof,
            echo=echo,
            cycle=cycle,
            metadata=metadata,
            atlas_node=atlas_node,
            phantom_trace=phantom_trace,
        )

    def _record_event(
        self,
        *,
        key: str,
        message: str,
        status: str,
        proof: str | None,
        echo: str | None,
        cycle: str | None,
        metadata: Optional[Mapping[str, object]],
        atlas_node: str | None,
        phantom_trace: str | None,
    ) -> WeaveFragment:
        self.ensure_ready()
        payload: Mapping[str, object] = metadata or {}
        cycle_name = cycle or self._infer_cycle()
        fragment = self.repository.record_event(
            cycle=cycle_name,
            key=key,
            status=status,
            message=message,
            proof=proof,
            echo=echo,
            metadata=payload,
        )
        self.repository.record_link(
            key=key,
            atlas_node=atlas_node,
            phantom_trace=phantom_trace,
        )
        return fragment

    def _infer_cycle(self) -> str:
        now = datetime.now(timezone.utc)
        return now.strftime("cycle-%Y%m%d")

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------
    def snapshot(self, *, limit: int = 20) -> PulseWeaverSnapshot:
        self.ensure_ready()
        fragments = self.repository.list_recent_events(limit=limit)
        links = self.repository.list_links()
        counts = self._build_counts()
        phantom = self._load_phantom(limit=limit)
        cycle = fragments[0].cycle if fragments else None
        summary: Dict[str, object] = {
            "total": counts.total,
            "by_status": counts.by_status,
            "atlas_links": counts.atlas,
            "phantom_threads": counts.phantom,
        }
        snapshot = PulseWeaverSnapshot(
            schema=self.SNAPSHOT_SCHEMA,
            cycle=cycle,
            summary=summary,
            ledger=fragments,
            links=links,
            phantom=phantom,
        )
        payload = snapshot.to_dict()
        self._validator.validate(payload)
        return snapshot

    def _build_counts(self) -> _Counts:
        status_counts = self.repository.counts_by_status()
        total = sum(status_counts.values())
        atlas_counts = self.repository.atlas_link_counts()
        phantom_counts = self.repository.phantom_link_counts()
        return _Counts(total=total, by_status=status_counts, atlas=atlas_counts, phantom=phantom_counts)

    def _load_phantom(self, *, limit: int) -> List[Dict[str, object]]:
        path = self._phantom_history
        if not path.exists():
            return []
        try:
            entries: Iterable[Mapping[str, object]] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        phantom: List[Dict[str, object]] = []
        for item in list(entries)[-limit:]:
            timestamp = item.get("timestamp")
            message = item.get("message")
            if timestamp is None or message is None:
                continue
            phantom.append(
                {
                    "timestamp": float(timestamp),
                    "message": str(message),
                    "hash": str(item.get("hash", "")),
                }
            )
        return phantom


__all__ = ["PulseWeaverService", "PulseWeaverSnapshot"]
