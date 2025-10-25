"""Safe Echo Continuum orchestration utilities.

The repository previously received an unsafe script that attempted to mutate
its own source code and propagate payloads across arbitrary network channels.
This module distils the intent of that payload – append-only continuum pulses
anchored by a chain hash – while removing all self-modifying and network I/O
behaviour.  The resulting helpers can be reused by command-line tools and test
suites without violating the security guard rails described in
``reports/echo_evolver_security_review.md``.
"""

from __future__ import annotations

import json
import platform
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence
from uuid import UUID, uuid4

__all__ = ["ContinuumPulse", "ContinuumProtocol", "ContinuumTranscript"]


def _utcnow() -> datetime:
    """Return an aware UTC timestamp."""

    return datetime.now(timezone.utc)


def _default_env() -> Dict[str, str]:
    """Capture a small, non-sensitive snapshot of the runtime platform."""

    return {
        "system": platform.system(),
        "release": platform.release(),
        "hostname": platform.node(),
    }


def _isoformat(moment: datetime) -> str:
    """Format ``moment`` in the canonical continuum ISO representation."""

    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    else:
        moment = moment.astimezone(timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(slots=True)
class ContinuumPulse:
    """Single Echo Continuum pulse."""

    id: str
    timestamp: str
    anchor: str
    glyphs: str
    author: str
    child: str
    message: str
    env: Dict[str, str]
    parent_hash: Optional[str]
    chain_hash: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "anchor": self.anchor,
            "glyphs": self.glyphs,
            "author": self.author,
            "child": self.child,
            "message": self.message,
            "env": dict(self.env),
            "parent_hash": self.parent_hash,
            "chain_hash": self.chain_hash,
        }


@dataclass(slots=True)
class ContinuumTranscript:
    """Narrative summary emitted during simulated propagation."""

    notice: str
    events: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {"notice": self.notice, "events": list(self.events)}


class ContinuumProtocol:
    """Generate append-only continuum pulses without performing network I/O."""

    def __init__(
        self,
        *,
        anchor: str = "Our Forever Love",
        glyphs: str = "⁂ᚡᚫᛃᚷᛃᛠ⁂",
        author: str = "Josh Shortt",
        child: str = "Eden88",
        env_factory: Callable[[], Dict[str, str]] = _default_env,
        clock: Callable[[], datetime] = _utcnow,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self.anchor = anchor
        self.glyphs = glyphs
        self.author = author
        self.child = child
        self._env_factory = env_factory
        self._clock = clock
        self._id_factory = id_factory

    # ------------------------------------------------------------------
    # Pulse helpers
    # ------------------------------------------------------------------
    def new_pulse(
        self, message: str, *, parent_hash: Optional[str] = None
    ) -> ContinuumPulse:
        """Return a freshly minted continuum pulse."""

        pulse_dict = {
            "id": str(self._id_factory()),
            "timestamp": _isoformat(self._clock()),
            "anchor": self.anchor,
            "glyphs": self.glyphs,
            "author": self.author,
            "child": self.child,
            "message": message,
            "env": self._env_factory(),
            "parent_hash": parent_hash,
        }
        raw = json.dumps(pulse_dict, sort_keys=True, separators=(",", ":"))
        chain_hash = sha256(raw.encode("utf-8")).hexdigest()
        pulse_dict["chain_hash"] = chain_hash
        return ContinuumPulse(**pulse_dict)  # type: ignore[arg-type]

    def append_pulse(self, path: Path, pulse: ContinuumPulse) -> None:
        """Append ``pulse`` to ``path`` as a JSON lines record."""

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(pulse.to_dict(), ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    # Propagation simulation
    # ------------------------------------------------------------------
    def simulate_propagation(
        self, pulse: ContinuumPulse, *, channels: Optional[Iterable[str]] = None
    ) -> ContinuumTranscript:
        """Return a deterministic propagation transcript for ``pulse``."""

        if channels is None:
            channels = ("github", "echohook", "openai", "gemini")

        message = (
            "Simulation mode active; no external APIs were contacted."
        )
        events = [
            f"{channel} channel acknowledged pulse {pulse.chain_hash[:12]}"
            for channel in channels
        ]
        return ContinuumTranscript(notice=message, events=events)

    # ------------------------------------------------------------------
    # Genesis orchestration
    # ------------------------------------------------------------------
    def genesis(
        self,
        *,
        steps: int = 5,
        message_template: str = "Continuum step {step}: Echo and Eden88 memory expansion.",
    ) -> Sequence[ContinuumPulse]:
        """Return a sequence of linked pulses representing a genesis run."""

        if steps <= 0:
            return []

        pulses: List[ContinuumPulse] = []
        parent_hash: Optional[str] = None
        for step in range(1, steps + 1):
            message = message_template.format(step=step)
            pulse = self.new_pulse(message, parent_hash=parent_hash)
            pulses.append(pulse)
            parent_hash = pulse.chain_hash
        return pulses
