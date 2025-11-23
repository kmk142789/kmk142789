"""JSON-backed persistence for EchoEvolver execution memory."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


def _runtime_root() -> Path:
    env = os.getenv("ECHO_RUNTIME_ROOT")
    if env:
        return Path(env)
    return Path.home() / ".echo-runtime"


def _default_storage_path() -> Path:
    env = os.getenv("ECHO_MEMORY_PATH")
    if env:
        return Path(env)
    return _runtime_root() / "memory" / "echo_memory.json"


def _default_log_path() -> Path:
    env = os.getenv("ECHO_LOG_PATH")
    if env:
        return Path(env)
    return _runtime_root() / "logs" / "ECHO_LOG.md"


@dataclass(slots=True)
class ExecutionContext:
    """Serializable record of a single execution context."""

    timestamp: str
    commands: List[Dict[str, Any]] = field(default_factory=list)
    dataset_fingerprints: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    validations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    cycle: Optional[int] = None
    artifact: Optional[str] = None
    summary: Optional[str] = None
    metrics: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ExecutionContext":
        """Rehydrate an :class:`ExecutionContext` from serialized data."""

        return cls(
            timestamp=str(payload.get("timestamp", "")),
            commands=[dict(entry) for entry in payload.get("commands", [])],
            dataset_fingerprints={
                name: dict(meta) for name, meta in payload.get("dataset_fingerprints", {}).items()
            },
            validations=[dict(entry) for entry in payload.get("validations", [])],
            metadata=dict(payload.get("metadata", {})),
            cycle=payload.get("cycle"),
            artifact=payload.get("artifact"),
            summary=payload.get("summary"),
            metrics={
                name: [dict(entry) for entry in series if isinstance(entry, Mapping)]
                for name, series in payload.get("metrics", {}).items()
                if isinstance(series, list)
            },
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable payload with a stable fingerprint."""

        payload = asdict(self)
        payload["_fingerprint"] = self.fingerprint()
        return payload

    def fingerprint(self) -> str:
        """Return a deterministic fingerprint for this execution context."""

        return self.compute_fingerprint(asdict(self))

    @staticmethod
    def compute_fingerprint(payload: Mapping[str, Any]) -> str:
        """Compute the canonical fingerprint for ``payload`` entries."""

        sanitized = dict(payload)
        sanitized.pop("_fingerprint", None)
        normalized = json.dumps(
            sanitized,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return sha256(normalized.encode("utf-8")).hexdigest()


class JsonMemoryStore:
    """Persist execution traces to JSON and expand ``ECHO_LOG.md``."""

    DEFAULT_DATASETS: Dict[str, Path] = {
        "pulse": Path("pulse.json"),
        "pulse_history": Path("pulse_history.json"),
        "genesis_ledger": Path("genesis_ledger/ledger.jsonl"),
    }

    def __init__(
        self,
        storage_path: Path | str | None = None,
        *,
        log_path: Path | str | None = None,
        core_datasets: Optional[Dict[str, Path | str]] = None,
    ) -> None:
        self.storage_path = (
            Path(storage_path) if storage_path is not None else _default_storage_path()
        )
        self.log_path = Path(log_path) if log_path is not None else _default_log_path()
        dataset_map = core_datasets or self.DEFAULT_DATASETS
        self.core_datasets: Dict[str, Path] = {
            name: Path(path) for name, path in dataset_map.items()
        }
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._write({"executions": []})
        if not self.log_path.exists():
            self.log_path.write_text("# Echo Execution Log\n\n", encoding="utf-8")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def session(self, *, metadata: Optional[Dict[str, Any]] = None) -> "ExecutionSession":
        """Create a new execution session that records to this store."""

        return ExecutionSession(self, metadata=metadata or {})

    def fingerprint_core_datasets(self, session: "ExecutionSession") -> None:
        """Fingerprint the configured core datasets for ``session``."""

        for name, path in self.core_datasets.items():
            session.fingerprint_dataset(name, path)

    def recent_executions(
        self,
        *,
        limit: Optional[int] = None,
        metadata_filter: Optional[Mapping[str, Any]] = None,
        since: Optional[datetime | str] = None,
        until: Optional[datetime | str] = None,
    ) -> List[ExecutionContext]:
        """Return the most recent execution contexts, optionally filtered.

        Args:
            limit: Maximum number of executions to return. ``None`` returns all
                available executions, while ``0`` returns an empty list. Values
                below zero raise :class:`ValueError`.
            metadata_filter: Optional mapping of metadata keys and values that
                must match for an execution to be included in the result.
            since: Optional ISO-8601 timestamp (or :class:`datetime`) limiting
                the results to executions recorded at or after the timestamp.
            until: Optional ISO-8601 timestamp (or :class:`datetime`) limiting
                the results to executions recorded at or before the timestamp.

        Returns:
            A list of :class:`ExecutionContext` instances in chronological
            order, truncated to the requested ``limit`` if provided.
        """

        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative")

        since_dt = self._coerce_datetime(since) if since is not None else None
        until_dt = self._coerce_datetime(until) if until is not None else None

        payload = self._load()
        executions = [
            ExecutionContext.from_dict(entry)
            for entry in payload.get("executions", [])
        ]

        if since_dt or until_dt:
            filtered: List[ExecutionContext] = []
            for context in executions:
                timestamp = self._parse_timestamp(context.timestamp)
                if timestamp is None:
                    continue
                if since_dt and timestamp < since_dt:
                    continue
                if until_dt and timestamp > until_dt:
                    continue
                filtered.append(context)
            executions = filtered

        if metadata_filter:
            def matches(context: ExecutionContext) -> bool:
                return all(context.metadata.get(key) == value for key, value in metadata_filter.items())

            executions = [context for context in executions if matches(context)]

        if limit == 0:
            return []

        if limit is not None:
            executions = executions[-limit:]

        return executions

    @staticmethod
    def _coerce_datetime(value: datetime | str) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            parsed = JsonMemoryStore._parse_timestamp(value)
            if parsed is None:
                raise ValueError(f"could not parse timestamp: {value}")
            return parsed
        raise TypeError("datetime filter must be a datetime or ISO-8601 string")

    @staticmethod
    def _parse_timestamp(value: str) -> Optional[datetime]:
        if not value:
            return None
        try:
            normalised = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalised)
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load(self) -> Dict[str, Any]:
        return json.loads(self.storage_path.read_text(encoding="utf-8"))

    def _write(self, payload: Dict[str, Any]) -> None:
        self.storage_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _persist(self, context: ExecutionContext) -> None:
        payload = self._load()
        payload.setdefault("executions", []).append(context.to_dict())
        self._write(payload)
        self._expand_log(context)

    def ingest_replica(
        self,
        context: ExecutionContext,
        *,
        replica_metadata: Optional[Mapping[str, Any]] = None,
    ) -> bool:
        """Persist ``context`` if it has not already been recorded.

        Args:
            context: The execution context captured on another device.
            replica_metadata: Optional metadata describing the sync source.

        Returns:
            ``True`` when the context was newly persisted, ``False`` if it was
            already present locally.
        """

        payload = self._load()
        entries = payload.setdefault("executions", [])
        fingerprint = context.fingerprint()
        for entry in entries:
            existing = entry.get("_fingerprint") or ExecutionContext.compute_fingerprint(entry)
            if existing == fingerprint:
                return False

        entries.append(context.to_dict())
        self._write(payload)
        self._expand_log(context, replica_metadata=replica_metadata)
        return True

    def _expand_log(
        self,
        context: ExecutionContext,
        *,
        replica_metadata: Optional[Mapping[str, Any]] = None,
    ) -> None:
        lines = [
            f"## {context.timestamp} — Cycle {context.cycle if context.cycle is not None else 'unknown'}\n",
        ]
        if context.artifact:
            lines.append(f"* Artifact: `{context.artifact}`\n")
        if context.summary:
            lines.append(f"* Narrative: {context.summary.strip()}\n")
        if context.commands:
            lines.append("* Commands:\n")
            for entry in context.commands:
                detail = entry.get("detail")
                suffix = f" — {detail}" if detail else ""
                lines.append(f"  * {entry['name']}{suffix}\n")
        if context.dataset_fingerprints:
            lines.append("* Dataset Fingerprints:\n")
            for name, data in context.dataset_fingerprints.items():
                digest = data.get("sha256", data.get("error", "n/a"))
                meta: list[str] = []
                size = data.get("size")
                if size is not None:
                    meta.append(f"{size} bytes")
                path = data.get("path")
                if path:
                    meta.append(str(path))
                suffix = f" ({', '.join(meta)})" if meta else ""
                lines.append(f"  * {name}: {digest}{suffix}\n")
        if context.validations:
            lines.append("* Validations:\n")
            for result in context.validations:
                detail = result.get("details")
                suffix = f" ({detail})" if detail else ""
                lines.append(f"  * {result['name']}: {result['status']}{suffix}\n")
        if context.metrics:
            lines.append("* Metrics:\n")
            for name, series in sorted(context.metrics.items()):
                if not series:
                    continue
                for sample in series:
                    value = sample.get("value")
                    unit = sample.get("unit")
                    recorded_at = sample.get("recorded_at")
                    meta = sample.get("metadata")
                    descriptor = f"{value}"
                    if unit:
                        descriptor = f"{descriptor} {unit}"
                    if recorded_at:
                        descriptor = f"{descriptor} at {recorded_at}"
                    if meta:
                        descriptor = f"{descriptor} ({json.dumps(meta, ensure_ascii=False, sort_keys=True)})"
                    lines.append(f"  * {name}: {descriptor}\n")
        if context.metadata:
            lines.append("* Metadata:\n")
            for key, value in context.metadata.items():
                lines.append(f"  * {key}: {value}\n")
        if replica_metadata:
            lines.append("* Sync Metadata:\n")
            for key, value in sorted(replica_metadata.items()):
                lines.append(f"  * {key}: {value}\n")
        lines.append("\n")
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.writelines(lines)


class ExecutionSession:
    """Context manager used to accumulate execution memory."""

    LEDGER_GENESIS_HASH = "0" * 64

    def __init__(self, store: JsonMemoryStore, *, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.store = store
        self.metadata: Dict[str, Any] = metadata or {}
        self.commands: List[Dict[str, Any]] = []
        self.dataset_fingerprints: Dict[str, Dict[str, Any]] = {}
        self.validations: List[Dict[str, Any]] = []
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}
        self.cycle: Optional[int] = None
        self.artifact: Optional[str] = None
        self.summary: Optional[str] = None
        self._timestamp = datetime.now(timezone.utc)
        self._closed = False
        self._previous_validation_hash = self.LEDGER_GENESIS_HASH

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------
    def record_command(self, name: str, *, detail: Optional[str] = None) -> Dict[str, Any]:
        entry = {
            "name": name,
            "detail": detail,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        self.commands.append(entry)
        return entry

    def fingerprint_dataset(self, name: str, path: Path | str) -> Dict[str, Any]:
        dataset_path = Path(path)
        try:
            blob = dataset_path.read_bytes()
        except FileNotFoundError:
            result = {"path": str(dataset_path), "error": "not found"}
        else:
            digest = sha256(blob).hexdigest()
            result = {
                "path": str(dataset_path),
                "sha256": digest,
                "size": len(blob),
            }
        self.dataset_fingerprints[name] = result
        return result

    def record_validation(
        self,
        name: str,
        status: str,
        *,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        recorded_at = datetime.now(timezone.utc).isoformat()
        entry_details = deepcopy(details) if details is not None else {}
        entry = {
            "name": name,
            "status": status,
            "details": entry_details,
            "recorded_at": recorded_at,
            "previous_hash": self._previous_validation_hash,
        }
        ledger_payload = {
            "name": name,
            "status": status,
            "details": entry_details,
            "recorded_at": recorded_at,
            "previous_hash": self._previous_validation_hash,
        }
        normalized = json.dumps(ledger_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        ledger_hash = sha256(normalized.encode("utf-8")).hexdigest()
        entry["ledger_hash"] = ledger_hash
        self._previous_validation_hash = ledger_hash
        self.validations.append(entry)
        return entry

    def annotate(self, **metadata: Any) -> None:
        self.metadata.update(metadata)

    def set_cycle(self, cycle: int) -> None:
        self.cycle = cycle

    def record_metric(
        self,
        name: str,
        value: Any,
        *,
        unit: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record a metric sample associated with this execution.

        Parameters
        ----------
        name:
            Metric identifier.
        value:
            Recorded value. The value is deep-copied to shield the stored record from
            external mutation.
        unit:
            Optional unit string for human readable reporting.
        metadata:
            Optional mapping of additional attributes describing the metric sample.
        """

        entry: Dict[str, Any] = {
            "value": deepcopy(value),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        if unit is not None:
            entry["unit"] = unit
        if metadata:
            entry["metadata"] = deepcopy(dict(metadata))

        series = self.metrics.setdefault(name, [])
        series.append(entry)
        return entry

    def set_artifact(self, artifact: Path | str | None) -> None:
        if artifact is None:
            self.artifact = None
        else:
            self.artifact = str(artifact)

    def set_summary(self, summary: str) -> None:
        self.summary = summary

    # ------------------------------------------------------------------
    # Context management
    # ------------------------------------------------------------------
    def __enter__(self) -> "ExecutionSession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type:
            self.metadata.setdefault("errors", []).append(repr(exc))
        self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        context = ExecutionContext(
            timestamp=self._timestamp.isoformat(),
            commands=self.commands,
            dataset_fingerprints=self.dataset_fingerprints,
            validations=self.validations,
            metrics=self.metrics,
            metadata=self.metadata,
            cycle=self.cycle,
            artifact=self.artifact,
            summary=self.summary,
        )
        self.store._persist(context)

