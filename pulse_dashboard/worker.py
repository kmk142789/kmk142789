"""Worker hive utilities for instrumenting CLI commands."""
from __future__ import annotations

import json
import time
import uuid
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, MutableMapping


@dataclass(slots=True)
class WorkerHiveConfig:
    """Filesystem configuration for worker hive telemetry."""

    root: Path = field(default_factory=Path.cwd)

    @property
    def state_dir(self) -> Path:
        return self.root / "state" / "pulse_dashboard"

    @property
    def log_path(self) -> Path:
        return self.state_dir / "worker_events.jsonl"


class WorkerHive:
    """Record command execution telemetry for visualisation on the dashboard."""

    def __init__(self, project_root: Path | str | None = None) -> None:
        self._config = WorkerHiveConfig(root=Path(project_root or Path.cwd()).resolve())
        self._config.state_dir.mkdir(parents=True, exist_ok=True)
        self._config.log_path.touch(exist_ok=True)

    @property
    def log_path(self) -> Path:
        """Return the path where worker telemetry is persisted."""

        return self._config.log_path

    @contextmanager
    def worker(self, name: str, *, metadata: Mapping[str, Any] | None = None):
        """Context manager capturing lifecycle events for a command worker."""

        task_id = uuid.uuid4().hex
        start_event = self._build_event(
            task_id,
            status="start",
            name=name,
            metadata=metadata,
        )
        self._append(start_event)
        handle = WorkerTaskHandle(self, task_id=task_id, name=name)
        try:
            yield handle
        except Exception as exc:  # pragma: no cover - defensive
            if not handle.completed:
                handle.fail(error=str(exc))
            raise
        else:
            if not handle.completed:
                handle.succeed()

    def record(self, event: Mapping[str, Any]) -> None:
        self._append(event)

    def _append(self, event: Mapping[str, Any]) -> None:
        payload = dict(event)
        payload.setdefault("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        payload.setdefault("id", uuid.uuid4().hex)
        with self._config.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True))
            handle.write("\n")

    def _build_event(
        self,
        task_id: str,
        *,
        status: str,
        name: str,
        metadata: Mapping[str, Any] | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        event: dict[str, Any] = {
            "task_id": task_id,
            "status": status,
            "name": name,
        }
        if metadata:
            event["metadata"] = dict(metadata)
        if payload:
            event["payload"] = dict(payload)
        return event

    def tail_events(
        self,
        *,
        limit: int | None = None,
        since: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return the newest worker events respecting optional filters.

        Parameters
        ----------
        limit:
            Maximum number of events to return. ``None`` returns the entire log.
        since:
            ISO 8601 timestamp (``YYYY-MM-DDTHH:MM:SSZ``) used as a lower bound.
        """

        if limit is not None and limit < 1:
            raise ValueError("limit must be a positive integer")

        if limit is None:
            events: list[dict[str, Any]] = []
            append_event = events.append
        else:
            events_deque: deque[dict[str, Any]] = deque(maxlen=limit)
            append_event = events_deque.append

        since_marker = since
        with self._config.log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:  # pragma: no cover - defensive guard
                    continue
                timestamp = event.get("timestamp")
                if since_marker and timestamp and timestamp < since_marker:
                    continue
                append_event(event)

        if limit is None:
            return events
        return list(events_deque)


class WorkerTaskHandle:
    """Lifecycle controller for a worker invocation."""

    def __init__(self, hive: WorkerHive, *, task_id: str, name: str) -> None:
        self._hive = hive
        self._task_id = task_id
        self._name = name
        self.completed = False

    @property
    def task_id(self) -> str:
        """Identifier linking the handle to the persisted worker events."""

        return self._task_id

    def progress(self, **payload: Any) -> None:
        """Emit a progress heartbeat for the active worker."""

        event = self._hive._build_event(
            self._task_id,
            status="progress",
            name=self._name,
            payload=payload,
        )
        self._hive.record(event)

    def succeed(self, **payload: Any) -> None:
        self._complete("success", payload)

    def fail(self, *, error: str | None = None, **payload: Any) -> None:
        data: MutableMapping[str, Any] = dict(payload)
        if error is not None:
            data["error"] = error
        self._complete("failure", data)

    def skip(self, **payload: Any) -> None:
        self._complete("skipped", payload)

    def _complete(self, status: str, payload: Mapping[str, Any] | None) -> None:
        if self.completed:
            return
        event = self._hive._build_event(
            self._task_id,
            status=status,
            name=self._name,
            payload=payload,
        )
        self._hive.record(event)
        self.completed = True


__all__ = ["WorkerHive", "WorkerTaskHandle"]
