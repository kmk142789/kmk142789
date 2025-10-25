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
import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, MutableMapping, Optional, Sequence

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
        self._trace_files = {
            "github": self.trace_root / "github_actions.log",
            "firebase": self.trace_root / "firebase_traces.json",
            "avatars": self.trace_root / "avatars.txt",
        }
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

        def _run() -> None:
            worker.status = "running"
            worker.started_at = time.time()
            try:
                kwargs.setdefault("kernel", self)
                worker.result = task(*args, **kwargs)
                worker.status = "complete"
            except Exception as exc:  # pragma: no cover - defensive path
                worker.result = exc
                worker.status = "failed"
            finally:
                worker.finished_at = time.time()

        thread = threading.Thread(target=_run, daemon=True)
        worker._thread = thread
        self.workers[identifier] = worker
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
