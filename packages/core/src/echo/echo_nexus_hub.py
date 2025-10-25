"""Central dashboard utilities for the Echo Visionary Kernel."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .echo_visionary_kernel import EchoVisionaryKernel, LogEntry


@dataclass(slots=True)
class WorkerStory:
    """Snapshot of a worker bot including live logs and story metadata."""

    identifier: str
    name: str
    role: str
    status: str
    started_at: Optional[float]
    finished_at: Optional[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    logs: List[LogEntry] = field(default_factory=list)
    outputs: List[Any] = field(default_factory=list)
    result: Any = None
    story_path: Optional[str] = None


@dataclass(slots=True)
class ScheduleLoopDigest:
    """Aggregate view of scheduler activity."""

    attempts: int
    successes: int
    failures: int
    recent: List[LogEntry] = field(default_factory=list)


class EchoNexusHub:
    """Expose a dashboard-friendly view of the kernel's internal state."""

    def __init__(self, kernel: EchoVisionaryKernel) -> None:
        self.kernel = kernel

    def snapshot(self) -> Dict[str, Any]:
        """Return a serialisable snapshot for dashboards and APIs."""

        workers = [self._build_worker_story(payload) for payload in self.kernel.all_worker_states()]
        schedule_summary = self.kernel.schedule_summary()
        schedule = ScheduleLoopDigest(
            attempts=schedule_summary["attempts"],
            successes=schedule_summary["successes"],
            failures=schedule_summary["failures"],
            recent=schedule_summary["recent"],
        )
        return {
            "workers": [asdict(worker) for worker in workers],
            "schedule": asdict(schedule),
            "stories_directory": str(self.kernel.worker_story_dir),
        }

    def peek_worker(self, identifier: str, *, limit: Optional[int] = None) -> List[LogEntry]:
        """Return recent log entries for ``identifier``."""

        return self.kernel.peek_worker(identifier, limit=limit)

    def worker_story_path(self, identifier: str) -> Optional[str]:
        """Return the on-disk story file for ``identifier`` if it exists."""

        state = self.kernel.worker_state(identifier)
        return state.get("story_path")

    def _build_worker_story(self, payload: Dict[str, Any]) -> WorkerStory:
        return WorkerStory(
            identifier=payload["identifier"],
            name=payload["name"],
            role=payload["role"],
            status=payload["status"],
            started_at=payload.get("started_at"),
            finished_at=payload.get("finished_at"),
            metadata=payload.get("metadata", {}),
            logs=payload.get("logs", []),
            outputs=payload.get("outputs", []),
            result=payload.get("result"),
            story_path=payload.get("story_path"),
        )
