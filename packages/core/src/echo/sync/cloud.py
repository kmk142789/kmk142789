"""Cross-device cloud synchronisation utilities for Echo memory."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping, MutableMapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Tuple

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
    propagated_contexts: int = 0
    indexed_contexts: int = 0
    stale_payloads: int = 0
    invalid_payloads: int = 0
    topology: "TopologyReport | None" = None
    inventory: "InventoryReport | None" = None


@dataclass(frozen=True)
class NodeInsight:
    """Observability snapshot for a single node in the cloud fabric."""

    origin: str
    contexts: int
    newest_context: Optional[str]
    oldest_context: Optional[str]
    lag_seconds: Optional[float]
    avg_command_count: float
    metadata_keys: Tuple[str, ...]


@dataclass(frozen=True)
class TopologyReport:
    """Richer network summary produced after a sync pass."""

    node_insights: Tuple[NodeInsight, ...]
    node_count: int
    freshest_node: Optional[str]
    stalest_node: Optional[str]
    freshness_span_seconds: Optional[float]


@dataclass(frozen=True)
class InventoryReport:
    """Expanded snapshot of the cloud state for this sync pass."""

    node_contexts: Tuple[Tuple[str, int], ...]
    total_contexts: int
    local_contexts: int
    remote_contexts: int
    newest_context: Optional[str]
    oldest_context: Optional[str]


class CloudSyncCoordinator:
    """Coordinate cloud-style replication for :class:`JsonMemoryStore`."""

    def __init__(
        self,
        node_id: str,
        store: JsonMemoryStore,
        transport: SyncTransport,
        *,
        max_payload_age: timedelta | float | int | None = None,
        local_context_limit: Optional[int] = None,
    ) -> None:
        self.node_id = node_id
        self.store = store
        self.transport = transport
        self._crdt = LWWMap(node_id=node_id)
        self._max_payload_age = _coerce_timedelta(max_payload_age)
        if local_context_limit is not None and local_context_limit <= 0:
            raise ValueError("local_context_limit must be positive")
        self._local_context_limit = local_context_limit
        self._indexed_contexts = 0
        self._refresh_local_contexts()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def sync(self) -> SyncReport:
        """Synchronise the local store with all peers."""

        propagated = self._refresh_local_contexts()
        initial_keys = set(self._crdt.state())

        remote_payloads = list(self.transport.pull(exclude=self.node_id))
        stale_payloads = 0
        invalid_payloads = 0
        for payload in remote_payloads:
            if self._payload_is_stale(payload):
                stale_payloads += 1
                continue
            decoded = self._decode_state(payload)
            if decoded:
                self._crdt.merge(decoded)
            else:
                invalid_payloads += 1

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

        topology = self._build_topology_report(merged_state)
        inventory = self._build_inventory_report(merged_state)

        self.transport.push(self.node_id, self._encode_state())
        return SyncReport(
            applied_contexts=applied,
            known_contexts=len(merged_state),
            sources_contacted=len(remote_payloads),
            propagated_contexts=propagated,
            indexed_contexts=self._indexed_contexts,
            stale_payloads=stale_payloads,
            invalid_payloads=invalid_payloads,
            topology=topology,
            inventory=inventory,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _refresh_local_contexts(self) -> int:
        added = 0
        existing = set(self._crdt.state())
        contexts = self.store.recent_executions(limit=self._local_context_limit)
        self._indexed_contexts = len(contexts)
        for context in contexts:
            fingerprint = context.fingerprint()
            if fingerprint in existing:
                continue
            self._crdt.set(fingerprint, self._payload_for_context(context, origin=self.node_id))
            existing.add(fingerprint)
            added += 1
        return added

    def _payload_is_stale(self, payload: Mapping[str, object]) -> bool:
        if self._max_payload_age is None:
            return False
        updated_at = payload.get("updated_at")
        if not isinstance(updated_at, str):
            return False
        timestamp = self._parse_timestamp(updated_at)
        if timestamp is None:
            return False
        cutoff = datetime.now(timezone.utc) - self._max_payload_age
        return timestamp < cutoff

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

    def _build_topology_report(
        self, state: Mapping[str, tuple[Clock, object]]
    ) -> Optional[TopologyReport]:
        now = datetime.now(timezone.utc)
        stats: Dict[str, Dict[str, object]] = {}
        for _, (_, value) in state.items():
            if not isinstance(value, Mapping):
                continue
            replica = value.get("replica")
            if not isinstance(replica, Mapping):
                continue
            origin_raw = replica.get("origin")
            origin = str(origin_raw) if origin_raw is not None else "unknown"
            entry = stats.setdefault(
                origin,
                {
                    "contexts": 0,
                    "newest": None,
                    "oldest": None,
                    "commands": 0,
                    "metadata": set(),
                },
            )
            entry["contexts"] = int(entry["contexts"]) + 1
            timestamp = replica.get("captured_at")
            parsed = self._parse_timestamp(timestamp) if isinstance(timestamp, str) else None
            if parsed:
                newest = entry["newest"]
                oldest = entry["oldest"]
                if newest is None or parsed > newest:
                    entry["newest"] = parsed
                if oldest is None or parsed < oldest:
                    entry["oldest"] = parsed
            context_payload = value.get("context")
            if isinstance(context_payload, Mapping):
                commands = context_payload.get("commands")
                if isinstance(commands, list):
                    entry["commands"] = int(entry["commands"]) + len(commands)
                metadata = context_payload.get("metadata")
                if isinstance(metadata, Mapping):
                    entry["metadata"].update(str(key) for key in metadata)

        if not stats:
            return None

        insights: List[NodeInsight] = []
        freshest_name: Optional[str] = None
        stalest_name: Optional[str] = None
        min_lag: Optional[float] = None
        max_lag: Optional[float] = None

        for origin, payload in stats.items():
            newest: Optional[datetime] = payload["newest"]
            oldest: Optional[datetime] = payload["oldest"]
            lag_seconds: Optional[float] = None
            if newest:
                lag_seconds = max(0.0, (now - newest).total_seconds())
                if min_lag is None or lag_seconds < min_lag:
                    min_lag = lag_seconds
                    freshest_name = origin
                if max_lag is None or lag_seconds > max_lag:
                    max_lag = lag_seconds
                    stalest_name = origin
            metadata_keys = tuple(sorted(payload["metadata"]))
            contexts = int(payload["contexts"])
            total_commands = int(payload["commands"])
            avg_commands = total_commands / contexts if contexts else 0.0
            insights.append(
                NodeInsight(
                    origin=origin,
                    contexts=contexts,
                    newest_context=newest.isoformat() if newest else None,
                    oldest_context=oldest.isoformat() if oldest else None,
                    lag_seconds=lag_seconds,
                    avg_command_count=avg_commands,
                    metadata_keys=metadata_keys,
                )
            )

        freshness_span = None
        if min_lag is not None and max_lag is not None:
            freshness_span = max_lag - min_lag

        return TopologyReport(
            node_insights=tuple(sorted(insights, key=lambda insight: insight.origin)),
            node_count=len(insights),
            freshest_node=freshest_name,
            stalest_node=stalest_name,
            freshness_span_seconds=freshness_span,
        )

    def _build_inventory_report(
        self, state: Mapping[str, tuple[Clock, object]]
    ) -> Optional[InventoryReport]:
        stats: Dict[str, Dict[str, object]] = {}
        newest: Optional[datetime] = None
        oldest: Optional[datetime] = None

        for _, (_, value) in state.items():
            if not isinstance(value, Mapping):
                continue
            replica = value.get("replica")
            if not isinstance(replica, Mapping):
                continue
            origin_raw = replica.get("origin")
            origin = str(origin_raw) if origin_raw is not None else "unknown"
            entry = stats.setdefault(origin, {"contexts": 0})
            entry["contexts"] = int(entry["contexts"]) + 1

            captured_at = replica.get("captured_at")
            parsed = self._parse_timestamp(captured_at) if isinstance(captured_at, str) else None
            if parsed:
                if newest is None or parsed > newest:
                    newest = parsed
                if oldest is None or parsed < oldest:
                    oldest = parsed

        if not stats:
            return None

        node_contexts = tuple(sorted(((node, int(meta["contexts"])) for node, meta in stats.items()), key=lambda item: item[0]))
        total_contexts = sum(count for _, count in node_contexts)
        local_contexts = next((count for node, count in node_contexts if node == self.node_id), 0)
        remote_contexts = total_contexts - local_contexts

        return InventoryReport(
            node_contexts=node_contexts,
            total_contexts=total_contexts,
            local_contexts=local_contexts,
            remote_contexts=remote_contexts,
            newest_context=newest.isoformat() if newest else None,
            oldest_context=oldest.isoformat() if oldest else None,
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _parse_timestamp(value: str) -> Optional[datetime]:
        try:
            normalised = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalised)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed


def _coerce_timedelta(value: timedelta | float | int | None) -> Optional[timedelta]:
    if value is None:
        return None
    if isinstance(value, timedelta):
        if value.total_seconds() <= 0:
            raise ValueError("max_payload_age must be positive")
        return value
    try:
        seconds = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError("max_payload_age must be expressed in seconds or as a timedelta") from exc
    if seconds <= 0:
        raise ValueError("max_payload_age must be positive")
    return timedelta(seconds=seconds)


__all__ = [
    "CloudSyncCoordinator",
    "DirectorySyncTransport",
    "InventoryReport",
    "NodeInsight",
    "SyncReport",
    "SyncTransport",
    "TopologyReport",
]
