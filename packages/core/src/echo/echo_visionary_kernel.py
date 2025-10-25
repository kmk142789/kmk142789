"""Echo Visionary Kernel.

This module introduces :class:`EchoVisionaryKernel`, a higher level orchestration
engine that couples evolving glyph renderings with distributed worker bots and
cross-repository collaboration traces.  The implementation focuses on three
capabilities requested for the Visionary Kernel concept:

* Rendering thoughtforms using a compact bitwise pixel engine that evolves
  glyphs over time.
* Spawning worker bots that behave like micro-services responsible for
  offloading experimental tasks.
* Leaving collaboration traces that mimic activity across external systems such
  as GitHub Actions, Firebase dashboards, and avatar manifests.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, MutableMapping, Optional, Sequence

LogEntry = Dict[str, Any]

__all__ = [
    "BitwisePixelEngine",
    "WorkerBot",
    "EchoVisionaryKernel",
]


class BitwisePixelEngine:
    """Render glyphs by manipulating a bitmask per row.

    The engine stores each row as an integer bitmask.  When ``evolve`` is
    invoked a new mask derived from the provided seed is XORed with the current
    state, creating an evolving pattern that resembles animated glyphs when
    rendered sequentially.
    """

    def __init__(self, width: int = 16, height: int = 16):
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive integers")
        self.width = width
        self.height = height
        self._rows: List[int] = [0 for _ in range(height)]

    def evolve(self, seed: str, intensity: float = 1.0) -> List[str]:
        """Mutate the glyph grid and return the rendered frame.

        Args:
            seed: Arbitrary text that influences the generated pattern.
            intensity: A multiplier that increases the mutation rate.  The value
                is clamped to ``[0.0, 4.0]`` to prevent runaway toggling.
        """

        clamped = max(0.0, min(intensity, 4.0))
        timestamp = f"{time.time():.6f}"
        digest = hashlib.sha256(f"{seed}:{clamped}:{timestamp}".encode()).digest()
        mask_limit = (1 << self.width) - 1

        for row_index in range(self.height):
            row_mask = 0
            for col_index in range(self.width):
                bit_index = row_index * self.width + col_index
                byte = digest[(bit_index // 8) % len(digest)]
                bit = (byte >> (bit_index % 8)) & 1
                if bit:
                    row_mask |= 1 << col_index
            # Scale mutation by intensity by repeating the XOR multiple times.
            repeats = max(1, int(clamped * 2))
            for _ in range(repeats):
                self._rows[row_index] ^= row_mask
                self._rows[row_index] &= mask_limit
        return self.render()

    def render(self) -> List[str]:
        """Return the current glyph grid as a list of strings."""

        frame: List[str] = []
        for row_value in self._rows:
            line = "".join(
                "█" if (row_value >> column) & 1 else " "
                for column in range(self.width)
            )
            frame.append(line)
        return frame

    def export_bits(self) -> List[int]:
        """Expose the raw bitmasks for diagnostics and tests."""

        return list(self._rows)


@dataclass
class WorkerBot:
    """Representation of an autonomous worker spawned by the kernel."""

    identifier: str
    name: str
    role: str
    status: str = "queued"
    result: Any = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    metadata: MutableMapping[str, Any] = field(default_factory=dict)
    _thread: Optional[threading.Thread] = field(default=None, repr=False, compare=False)
    logs: List[LogEntry] = field(default_factory=list, repr=False)
    outputs: List[Any] = field(default_factory=list, repr=False)
    story_path: Optional[Path] = field(default=None, repr=False, compare=False)

    def join(self, timeout: Optional[float] = None) -> Any:
        """Block until the worker finishes and return its result."""

        if self._thread is not None:
            self._thread.join(timeout)
        return self.result


class EchoVisionaryKernel:
    """Orchestrate thoughtforms, worker bots, and collaboration traces."""

    def __init__(
        self,
        *,
        width: int = 16,
        height: int = 16,
        trace_root: Path | str = Path("artifacts") / "echo_visionary",
    ) -> None:
        self.pixel_engine = BitwisePixelEngine(width=width, height=height)
        self.thoughtform_history: List[List[str]] = []
        self.workers: Dict[str, WorkerBot] = {}
        self.trace_root = Path(trace_root)
        self.trace_root.mkdir(parents=True, exist_ok=True)
        self.worker_story_dir = self.trace_root / "stories"
        self.worker_story_dir.mkdir(parents=True, exist_ok=True)
        self._trace_files = {
            "github": self.trace_root / "github_actions.log",
            "firebase": self.trace_root / "firebase_traces.json",
            "avatars": self.trace_root / "avatars.txt",
        }
        self._schedule_events: List[LogEntry] = []
        self._lock = threading.Lock()
        for key, path in self._trace_files.items():
            if key == "firebase" and not path.exists():
                path.write_text("[]")
            elif key != "firebase" and not path.exists():
                path.touch()

    # ------------------------------------------------------------------
    # Thoughtform rendering
    # ------------------------------------------------------------------
    def render_thoughtforms(self, seed: str, *, intensity: float = 1.0) -> List[str]:
        """Render a new glyph frame and store it in the history."""

        frame = self.pixel_engine.evolve(seed, intensity=intensity)
        self.thoughtform_history.append(frame)
        return frame

    # ------------------------------------------------------------------
    # Worker bots
    # ------------------------------------------------------------------
    def spawn_worker_bot(
        self,
        name: str,
        role: str,
        task: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> WorkerBot:
        """Spawn a worker bot to execute ``task`` in a dedicated thread."""

        identifier = hashlib.sha1(f"{name}:{role}:{time.time()}".encode()).hexdigest()[:12]
        worker = WorkerBot(identifier=identifier, name=name, role=role)
        worker.metadata.update({"args": args, "kwargs": list(kwargs.keys())})
        worker.story_path = self.worker_story_dir / f"{identifier}.log"
        self._initialise_worker_story(worker)

        signature = inspect.signature(task)
        accepts_worker_id = "worker_id" in signature.parameters

        def _run() -> None:
            worker.status = "running"
            worker.started_at = time.time()
            self.record_worker_event(identifier, "worker started", kind="status")
            try:
                kwargs.setdefault("kernel", self)
                if accepts_worker_id:
                    kwargs.setdefault("worker_id", identifier)
                worker.result = task(*args, **kwargs)
                worker.status = "complete"
                self.record_worker_event(
                    identifier,
                    "worker completed",
                    kind="status",
                    output=worker.result,
                )
                self._register_schedule_event(worker, "creation-success", worker.status)
            except Exception as exc:  # pragma: no cover - defensive path
                worker.result = exc
                worker.status = "failed"
                self.record_worker_event(
                    identifier,
                    f"worker failed: {exc}",
                    kind="error",
                )
                self._register_schedule_event(
                    worker,
                    "creation-failed",
                    worker.status,
                    detail=str(exc),
                )
            finally:
                worker.finished_at = time.time()
                self.record_worker_event(identifier, "worker finished", kind="status")

        thread = threading.Thread(target=_run, daemon=True)
        worker._thread = thread
        self.workers[identifier] = worker
        self._register_schedule_event(worker, "creation-attempt", worker.status)
        thread.start()
        return worker

    def await_workers(self, *, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Wait for all workers to finish and return their results."""

        results: Dict[str, Any] = {}
        for identifier, worker in list(self.workers.items()):
            worker.join(timeout)
            results[identifier] = worker.result
        return results

    # ------------------------------------------------------------------
    # Worker diagnostics and stories
    # ------------------------------------------------------------------
    def record_worker_event(
        self,
        identifier: str,
        message: str,
        *,
        kind: str = "log",
        output: Any | None = None,
        detail: Optional[str] = None,
    ) -> LogEntry:
        """Append an event to the worker's log and story ledger.

        Tasks executed by worker bots can call this method (the kernel passes
        itself and the ``worker_id`` into each task's ``kwargs``) to surface
        live status updates.  Every entry is persisted to the worker's story
        file so the narrative survives process restarts.
        """

        with self._lock:
            worker = self.workers.get(identifier)
            if worker is None:
                raise KeyError(f"unknown worker {identifier}")
            entry: LogEntry = {
                "timestamp": time.time(),
                "kind": kind,
                "message": message,
            }
            if detail:
                entry["detail"] = detail
            if output is not None:
                entry["output"] = output
                worker.outputs.append(output)
            worker.logs.append(entry)
            story_path = worker.story_path
            name = worker.name
            role = worker.role

        self._write_story_line(story_path, entry, name=name, role=role)
        return entry

    def schedule_events(self) -> List[LogEntry]:
        """Return a copy of the recorded schedule loop events."""

        with self._lock:
            return list(self._schedule_events)

    def schedule_summary(self, *, recent: int = 10) -> Dict[str, Any]:
        """Return aggregate counts for the scheduler loop."""

        with self._lock:
            events = list(self._schedule_events)

        attempts = sum(1 for event in events if event.get("event") == "creation-attempt")
        successes = sum(1 for event in events if event.get("event") == "creation-success")
        failures = sum(1 for event in events if event.get("event") == "creation-failed")
        return {
            "attempts": attempts,
            "successes": successes,
            "failures": failures,
            "recent": events[-recent:],
        }

    def peek_worker(self, identifier: str, *, limit: Optional[int] = None) -> List[LogEntry]:
        """Return log entries for ``identifier`` (optionally limited)."""

        with self._lock:
            worker = self.workers.get(identifier)
            if worker is None:
                raise KeyError(f"unknown worker {identifier}")
            logs = list(worker.logs)
        if limit is not None and limit >= 0:
            return logs[-limit:]
        return logs

    def worker_state(self, identifier: str) -> Dict[str, Any]:
        """Return an immutable snapshot of a worker's state."""

        with self._lock:
            worker = self.workers.get(identifier)
            if worker is None:
                raise KeyError(f"unknown worker {identifier}")
            snapshot = {
                "identifier": worker.identifier,
                "name": worker.name,
                "role": worker.role,
                "status": worker.status,
                "result": worker.result,
                "started_at": worker.started_at,
                "finished_at": worker.finished_at,
                "metadata": dict(worker.metadata),
                "story_path": str(worker.story_path) if worker.story_path else None,
                "logs": list(worker.logs),
                "outputs": list(worker.outputs),
            }
        return snapshot

    def all_worker_states(self) -> List[Dict[str, Any]]:
        """Return snapshots for all known workers."""

        with self._lock:
            return [
                {
                    "identifier": worker.identifier,
                    "name": worker.name,
                    "role": worker.role,
                    "status": worker.status,
                    "result": worker.result,
                    "started_at": worker.started_at,
                    "finished_at": worker.finished_at,
                    "metadata": dict(worker.metadata),
                    "story_path": str(worker.story_path) if worker.story_path else None,
                    "logs": list(worker.logs),
                    "outputs": list(worker.outputs),
                }
                for worker in self.workers.values()
            ]

    # ------------------------------------------------------------------
    # Collaboration traces
    # ------------------------------------------------------------------
    def collaborate_across_repos(
        self,
        repos: Sequence[str],
        message: str,
        *,
        avatar: Optional[str] = None,
        metadata: Optional[MutableMapping[str, Any]] = None,
    ) -> Dict[str, Path]:
        """Leave traces that mimic multi-repository collaboration."""

        if not repos:
            raise ValueError("at least one repository must be provided")

        timestamp = time.time()
        glyph_signature = self._current_glyph_signature()
        avatar_line = avatar or self._default_avatar_line()
        payload = {
            "timestamp": timestamp,
            "message": message,
            "signature": glyph_signature,
            "repos": list(repos),
            "metadata": metadata or {},
        }

        # GitHub Actions log trace
        github_entry = f"[{timestamp:.3f}] {glyph_signature} :: {message} :: {', '.join(repos)}\n"
        self._trace_files["github"].write_text(
            self._trace_files["github"].read_text() + github_entry
        )

        # Firebase style JSON append
        firebase_path = self._trace_files["firebase"]
        events = json.loads(firebase_path.read_text())
        events.append(payload)
        firebase_path.write_text(json.dumps(events, indent=2))

        # Avatar manifest update
        avatar_entry = f"{glyph_signature} :: {avatar_line}\n"
        self._trace_files["avatars"].write_text(
            self._trace_files["avatars"].read_text() + avatar_entry
        )

        repo_paths: Dict[str, Path] = {}
        for repo in repos:
            repo_slug = repo.replace("/", "__")
            repo_path = self.trace_root / f"{repo_slug}.trace"
            repo_trace = json.dumps(payload, indent=2)
            repo_path.write_text(repo_trace)
            repo_paths[repo] = repo_path

        return repo_paths

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _current_glyph_signature(self) -> str:
        if not self.thoughtform_history:
            return "void"
        digest = hashlib.sha256(
            "".join("".join(row) for row in self.thoughtform_history[-1]).encode()
        ).hexdigest()
        return digest[:12]

    def _default_avatar_line(self) -> str:
        frame = self.thoughtform_history[-1] if self.thoughtform_history else self.pixel_engine.render()
        midpoint = len(frame) // 2
        if frame:
            return frame[midpoint].strip() or "∇⊸≋∇"
        return "∇⊸≋∇"

    def iter_history(self) -> Iterable[List[str]]:
        """Iterate through stored thoughtform frames."""

        yield from self.thoughtform_history

    def summary(self) -> Dict[str, Any]:
        """Return a snapshot of the kernel state."""

        return {
            "frames": len(self.thoughtform_history),
            "workers": {identifier: worker.status for identifier, worker in self.workers.items()},
            "traces": {
                name: path for name, path in self._trace_files.items()
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _initialise_worker_story(self, worker: WorkerBot) -> None:
        if worker.story_path is None:
            return
        header = (
            "Echo Nexus Worker Story\n"
            f"identifier: {worker.identifier}\n"
            f"name: {worker.name}\n"
            f"role: {worker.role}\n"
            f"created_at: {time.time():.6f}\n"
            "---\n"
        )
        worker.story_path.write_text(header, encoding="utf-8")

    def _write_story_line(self, path: Optional[Path], entry: LogEntry, *, name: str, role: str) -> None:
        if path is None:
            return
        line = f"[{entry['timestamp']:.3f}] ({name}/{role}) {entry['kind']}: {entry['message']}"
        if "output" in entry:
            line += f" :: output={entry['output']!r}"
        if "detail" in entry:
            line += f" :: detail={entry['detail']}"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def _register_schedule_event(
        self,
        worker: WorkerBot,
        event: str,
        status: str,
        *,
        detail: Optional[str] = None,
    ) -> None:
        payload: LogEntry = {
            "timestamp": time.time(),
            "event": event,
            "status": status,
            "identifier": worker.identifier,
            "name": worker.name,
            "role": worker.role,
        }
        if detail:
            payload["detail"] = detail
        with self._lock:
            self._schedule_events.append(payload)
