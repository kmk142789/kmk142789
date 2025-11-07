"""Tools for recording and validating governance pulse events.

This module keeps an append-only log that can be verified by anyone in the
network.  Each entry is chained to the previous entry through a SHA-256 digest
so tampering can be detected.  The API is intentionally lightweight: callers
only need to provide an event type and a JSON-serialisable payload.

Example
-------
>>> from echo.vNext.agents import governance_pulse
>>> governance_pulse.record("task_registered", {"task": "bootstrap"})
{'time': '2024-01-01T00:00:00+00:00', 'event': 'task_registered', ...}
>>> governance_pulse.verify()
True
"""

from __future__ import annotations

import contextlib
import dataclasses
import datetime as _dt
import hashlib
import json
import pathlib
import tempfile
from typing import Dict, Iterable, Iterator, List, Optional


__all__ = [
    "PulseEntry",
    "record",
    "load",
    "verify",
    "iter_entries",
]


pulse_file = pathlib.Path("echo/vNext/agents/pulse_log.json")


@dataclasses.dataclass(frozen=True)
class PulseEntry:
    """Representation of an immutable governance pulse log entry."""

    time: str
    event: str
    payload: Dict
    digest: str
    previous_digest: Optional[str] = None

    def to_dict(self) -> Dict:
        """Return a JSON-serialisable dictionary representation."""

        return {
            "time": self.time,
            "event": self.event,
            "payload": self.payload,
            "previous_digest": self.previous_digest,
            "digest": self.digest,
        }


def _canonical_json(data: Dict) -> str:
    """Serialise *data* deterministically for digest purposes."""

    return json.dumps(data, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def _compute_digest(entry_data: Dict) -> str:
    return hashlib.sha256(_canonical_json(entry_data).encode("utf-8")).hexdigest()


def _ensure_directory(path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _load_raw(path: pathlib.Path) -> List[Dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive coding
        raise ValueError(f"Pulse log {path} is corrupted") from exc


def record(event_type: str, payload: Dict, *, path: Optional[pathlib.Path] = None) -> PulseEntry:
    """Record a governance pulse *event_type* and *payload*.

    Parameters
    ----------
    event_type:
        A short string describing the action (e.g. ``"task_registered"``).
    payload:
        A JSON-serialisable mapping with event specific data.  Keys are sorted
        before hashing so that equivalent payloads always produce the same
        digest.
    path:
        Optional custom path for unit testing.  Defaults to :data:`pulse_file`.
    """

    log_path = pathlib.Path(path or pulse_file)
    _ensure_directory(log_path)

    existing = load(path=log_path)
    previous_digest = existing[-1].digest if existing else None

    timestamp = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
    entry_data = {
        "time": timestamp,
        "event": event_type,
        "payload": payload,
        "previous_digest": previous_digest,
    }
    digest = _compute_digest(entry_data)

    entry = PulseEntry(
        time=timestamp,
        event=event_type,
        payload=payload,
        previous_digest=previous_digest,
        digest=digest,
    )

    updated_log = [e.to_dict() for e in existing]
    updated_log.append(entry.to_dict())

    # Write atomically via a temporary file to guard against partial writes.
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
        json.dump(updated_log, tmp, indent=2, ensure_ascii=False)
        tmp.flush()
        tmp_path = pathlib.Path(tmp.name)

    tmp_path.replace(log_path)
    return entry


def load(*, path: Optional[pathlib.Path] = None) -> List[PulseEntry]:
    """Load the entire pulse log as :class:`PulseEntry` instances."""

    log_path = pathlib.Path(path or pulse_file)
    raw_entries = _load_raw(log_path)
    return [
        PulseEntry(
            time=str(item["time"]),
            event=str(item["event"]),
            payload=dict(item["payload"]),
            previous_digest=item.get("previous_digest"),
            digest=str(item["digest"]),
        )
        for item in raw_entries
    ]


def iter_entries(*, path: Optional[pathlib.Path] = None) -> Iterator[PulseEntry]:
    """Iterate over pulse entries without loading the whole file at once."""

    for entry in load(path=path):
        yield entry


def verify(*, entries: Optional[Iterable[PulseEntry]] = None, path: Optional[pathlib.Path] = None) -> bool:
    """Return ``True`` if the pulse log forms an unbroken digest chain."""

    if entries is None:
        entries = load(path=path)

    previous_digest: Optional[str] = None
    for entry in entries:
        expected_data = {
            "time": entry.time,
            "event": entry.event,
            "payload": entry.payload,
            "previous_digest": previous_digest,
        }
        expected_digest = _compute_digest(expected_data)
        if entry.digest != expected_digest:
            return False
        previous_digest = entry.digest
    return True


@contextlib.contextmanager
def using_log(path: pathlib.Path) -> Iterator[pathlib.Path]:
    """Context manager that temporarily swaps :data:`pulse_file` for *path*.

    This is primarily useful for unit tests that should run without mutating
    the real governance pulse log on disk.
    """

    global pulse_file
    original = pulse_file
    pulse_file = path
    try:
        yield path
    finally:
        pulse_file = original


if __name__ == "__main__":  # pragma: no cover - manual debugging helper
    sample = {
        "task": "Implement next-wave scaffold setup",
        "steward": "kmk142789",
        "alignment": "Echo Capability Charter vNext §3.2",
    }
    entry = record("task_registered", sample)
    print(json.dumps(entry.to_dict(), indent=2, ensure_ascii=False))
    print(f"Verified: {verify()}")
