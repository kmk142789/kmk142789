"""Cross-device cloud synchronisation utilities for Echo memory."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping, MutableMapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Protocol

from ..crdt.lww import Clock, LWWMap
from ..memory.store import ExecutionContext, JsonMemoryStore


class SyncTransport(Protocol):
    """Protocol describing storage used to exchange CRDT states."""

    def push(self, node_id: str, payload: Mapping[str, object]) -> None:
        """Publish ``payload`` for ``node_id`` to the transport layer."""

    def pull(self, *, exclude: Optional[str] = None) -> Iterable[Mapping[str, object]]:
        """Yield payloads available on the transport layer."""


class DirectorySyncTransport:
    """Transport that persists CRDT states to a shared directory."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def push(self, node_id: str, payload: Mapping[str, object]) -> None:
        path = self.root / f"{node_id}.json"
        temp_path = path.with_suffix(".json.tmp")
        temp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temp_path.replace(path)

    def pull(self, *, exclude: Optional[str] = None) -> Iterator[Mapping[str, object]]:
        for candidate in sorted(self.root.glob("*.json")):
            if exclude and candidate.stem == exclude:
                continue
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if isinstance(data, MutableMapping):
                yield data


@dataclass(frozen=True)
class SyncReport:
    """Summary of a synchronisation pass."""

    applied_contexts: int
    known_contexts: int
    sources_contacted: int


class CloudSyncCoordinator:
    """Coordinate cloud-style replication for :class:`JsonMemoryStore`."""

    def __init__(
        self,
        node_id: str,
        store: JsonMemoryStore,
        transport: SyncTransport,
    ) -> None:
        self.node_id = node_id
        self.store = store
        self.transport = transport
        self._crdt = LWWMap(node_id=node_id)
        self._refresh_local_contexts()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def sync(self) -> SyncReport:
        """Synchronise the local store with all peers."""

        self._refresh_local_contexts()
        initial_keys = set(self._crdt.state())

        remote_payloads = list(self.transport.pull(exclude=self.node_id))
        for payload in remote_payloads:
            decoded = self._decode_state(payload)
            if decoded:
                self._crdt.merge(decoded)

        merged_state = self._crdt.state()
        new_keys = set(merged_state) - initial_keys

        applied = 0
        for key in new_keys:
            _, value = merged_state[key]
            if not isinstance(value, MutableMapping):
                continue
            context_payload = value.get("context")
            if not isinstance(context_payload, Mapping):
                continue
            context = ExecutionContext.from_dict(context_payload)
            replica_meta = value.get("replica")
            if self.store.ingest_replica(context, replica_metadata=replica_meta):
                applied += 1

        self.transport.push(self.node_id, self._encode_state())
        return SyncReport(
            applied_contexts=applied,
            known_contexts=len(merged_state),
            sources_contacted=len(remote_payloads),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _refresh_local_contexts(self) -> int:
        added = 0
        existing = set(self._crdt.state())
        for context in self.store.recent_executions():
            fingerprint = context.fingerprint()
            if fingerprint in existing:
                continue
            self._crdt.set(fingerprint, self._payload_for_context(context, origin=self.node_id))
            existing.add(fingerprint)
            added += 1
        return added

    def _payload_for_context(self, context: ExecutionContext, *, origin: str) -> Dict[str, object]:
        return {
            "context": context.to_dict(),
            "replica": {
                "origin": origin,
                "captured_at": self._now(),
            },
        }

    def _encode_state(self) -> Dict[str, object]:
        state: Dict[str, object] = {}
        for key, (clock, value) in self._crdt.state().items():
            state[key] = {
                "clock": {"node": clock.node, "tick": clock.tick},
                "value": value,
            }
        return {"node": self.node_id, "updated_at": self._now(), "state": state}

    def _decode_state(self, payload: Mapping[str, object]) -> Dict[str, tuple[Clock, object]]:
        raw_state = payload.get("state")
        if not isinstance(raw_state, Mapping):
            return {}

        decoded: Dict[str, tuple[Clock, object]] = {}
        for key, entry in raw_state.items():
            if not isinstance(entry, Mapping):
                continue
            clock_data = entry.get("clock")
            value = entry.get("value")
            if not isinstance(clock_data, Mapping):
                continue
            node = clock_data.get("node")
            tick = clock_data.get("tick")
            if not isinstance(node, str):
                continue
            try:
                tick_int = int(tick)
            except (TypeError, ValueError):
                continue
            decoded[str(key)] = (Clock(node=node, tick=tick_int), value)
        return decoded

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()


__all__ = [
    "CloudSyncCoordinator",
    "DirectorySyncTransport",
    "SyncReport",
    "SyncTransport",
]
