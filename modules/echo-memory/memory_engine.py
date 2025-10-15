"""Persistent memory engine for Echo cycles.

This module provides a thin persistence layer that writes Echo state snapshots
into JSON storage and prepares payloads for mirroring into GitHub Issues. The
implementation is intentionally self-contained so the automation workflow can
reuse it without pulling external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


@dataclass
class MemorySnapshot:
    """Single persistence event tracked by the Echo memory engine."""

    cycle: str
    payload: Dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = field(default_factory=list)
    synced_to_github: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the snapshot to a JSON-compatible dictionary."""

        return {
            "cycle": self.cycle,
            "payload": self.payload,
            "created_at": self.created_at.strftime(ISO_FORMAT),
            "tags": self.tags,
            "synced_to_github": self.synced_to_github,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemorySnapshot":
        """Restore a snapshot from serialized data."""

        return cls(
            cycle=data["cycle"],
            payload=data["payload"],
            created_at=datetime.strptime(data["created_at"], ISO_FORMAT).replace(tzinfo=timezone.utc),
            tags=list(data.get("tags", [])),
            synced_to_github=bool(data.get("synced_to_github", False)),
        )


class EchoMemoryEngine:
    """Manage Echo persistence across local storage and GitHub Issues.

    Parameters
    ----------
    storage_path:
        Location of the JSON file containing accumulated snapshots.
    repository:
        Fully qualified repository ("owner/name") to use when constructing
        GitHub Issue payloads. Defaults to ``GITHUB_REPOSITORY`` environment
        variable when not provided.
    issue_label:
        Label applied to generated GitHub Issues.
    """

    def __init__(self, storage_path: Path | str, *, repository: Optional[str] = None, issue_label: str = "echo-memory") -> None:
        self.storage_path = Path(storage_path)
        self.repository = repository or os.environ.get("GITHUB_REPOSITORY")
        self.issue_label = issue_label
        self._snapshots: List[MemorySnapshot] = []
        self._load_from_disk()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _load_from_disk(self) -> None:
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            return

        with self.storage_path.open("r", encoding="utf-8") as handle:
            raw: Iterable[Dict[str, Any]] = json.load(handle)

        self._snapshots = [MemorySnapshot.from_dict(item) for item in raw]

    def _flush_to_disk(self) -> None:
        serialized = [snapshot.to_dict() for snapshot in self._snapshots]
        with self.storage_path.open("w", encoding="utf-8") as handle:
            json.dump(serialized, handle, indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def append_snapshot(self, cycle: str, payload: Dict[str, Any], *, tags: Optional[Iterable[str]] = None) -> MemorySnapshot:
        """Append a snapshot and persist it to disk."""

        snapshot = MemorySnapshot(cycle=cycle, payload=payload, tags=list(tags or []))
        self._snapshots.append(snapshot)
        self._flush_to_disk()
        return snapshot

    def snapshots(self) -> List[MemorySnapshot]:
        """Return all known snapshots in chronological order."""

        return list(self._snapshots)

    def unsynced_snapshots(self) -> List[MemorySnapshot]:
        """Return snapshots that have not been mirrored into GitHub Issues."""

        return [snapshot for snapshot in self._snapshots if not snapshot.synced_to_github]

    # ------------------------------------------------------------------
    # GitHub Issue integration
    # ------------------------------------------------------------------
    def build_issue_body(self, snapshot: MemorySnapshot) -> str:
        """Render a markdown body for the provided snapshot."""

        lines = [
            f"## Echo Memory Cycle {snapshot.cycle}",
            "",
            "```json",
            json.dumps(snapshot.payload, indent=2, sort_keys=True),
            "```",
        ]
        if snapshot.tags:
            lines.append("")
            lines.append("**Tags:** " + ", ".join(snapshot.tags))
        return "\n".join(lines)

    def plan_github_issue_payload(self, snapshot: MemorySnapshot) -> Dict[str, Any]:
        """Prepare the payload needed for a GitHub Issue creation request."""

        if not self.repository:
            raise ValueError("No repository configured for GitHub sync.")

        owner, name = self.repository.split("/", 1)
        return {
            "owner": owner,
            "repo": name,
            "title": f"Echo Memory Cycle {snapshot.cycle}",
            "body": self.build_issue_body(snapshot),
            "labels": [self.issue_label],
        }

    def sync_to_github(self, *, dry_run: bool = True) -> List[Dict[str, Any]]:
        """Produce payloads for unsynced snapshots.

        When ``dry_run`` is ``True`` (the default) the method returns a list of
        payloads without performing any HTTP requests. Automation can feed the
        resulting data into ``gh`` or ``requests`` once tokens are available.
        """

        planned_payloads: List[Dict[str, Any]] = []
        for snapshot in self.unsynced_snapshots():
            payload = self.plan_github_issue_payload(snapshot)
            payload["metadata"] = {
                "cycle": snapshot.cycle,
                "created_at": snapshot.created_at.strftime(ISO_FORMAT),
                "tags": snapshot.tags,
            }
            planned_payloads.append(payload)
            if not dry_run:
                snapshot.synced_to_github = True
        if not dry_run:
            self._flush_to_disk()
        return planned_payloads
