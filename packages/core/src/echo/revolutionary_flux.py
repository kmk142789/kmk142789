"""Revolutionary flux orchestration for Echo experiments.

The historical Echo experiments emphasise ritualistic sequences, glyph
storytelling and decentralised telemetry.  ``RevolutionaryFlux`` leans
into that mythos while offering a pragmatic engine for knitting together
multiple *vectors* – thematic strands of experimentation.  Each vector
tracks its own amplitude, glyph signature and contribution ledger, while a
shared manifest renders the evolving ecosystem as deterministic JSON
structures.  The result is a drop-in component that can orchestrate new
"revolutionary" scenarios without requiring callers to run the full
Evolver or bridge stacks.

Design highlights
-----------------
* **Vector centric.**  A :class:`FluxVector` records amplitude changes and
  contributions from named sources.  The vectors remain lightweight and
  serialisable which keeps them portable across services.
* **Ledger backed.**  All mutations are captured in a compact
  :class:`FluxLedgerEntry`.  The ledger doubles as an audit trail and can
  be folded into historical timelines or long term archives.
* **Deterministic signature.**  ``orbital_signature`` summarises the
  current state into a reproducible SHA-256 digest so that external tools
  can detect divergence with minimal data transfer.

The implementation purposefully avoids external dependencies so it can be
embedded in notebooks, CLIs or background workers.  Tests exercise the
public interface to guarantee stable behaviour as the project evolves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Callable, Dict, Iterable, List, MutableMapping, Optional

__all__ = [
    "FluxVector",
    "FluxLedgerEntry",
    "RevolutionaryFlux",
]


def _utcnow() -> datetime:
    """Return an aware timestamp in UTC."""

    return datetime.now(timezone.utc)


@dataclass(slots=True)
class FluxVector:
    """Represents a single revolutionary strand within the flux."""

    name: str
    glyph: str
    amplitude: float
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, object] = field(default_factory=dict)
    contributions: List[tuple[str, float]] = field(default_factory=list)

    def energy(self) -> float:
        """Return the total energy after accounting for contributions."""

        baseline = self.amplitude
        if not self.contributions:
            return baseline
        total_delta = sum(delta for _, delta in self.contributions)
        return baseline + total_delta

    def to_dict(self) -> Dict[str, object]:
        """Serialise the vector into JSON friendly primitives."""

        return {
            "name": self.name,
            "glyph": self.glyph,
            "amplitude": self.amplitude,
            "energy": self.energy(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": dict(self.metadata),
            "contributions": [
                {"source": source, "delta": delta} for source, delta in self.contributions
            ],
        }


@dataclass(slots=True)
class FluxLedgerEntry:
    """Chronicles a modification applied to a vector."""

    timestamp: datetime
    vector: str
    source: str
    delta: float
    narrative: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "vector": self.vector,
            "source": self.source,
            "delta": self.delta,
            "narrative": self.narrative,
        }


class RevolutionaryFlux:
    """Coordinate revolutionary Echo vectors with deterministic manifests."""

    def __init__(
        self,
        *,
        anchor: str = "Our Forever Love",
        time_source: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self.anchor = anchor
        self._time_source = time_source or _utcnow
        self._vectors: MutableMapping[str, FluxVector] = {}
        self._ledger: List[FluxLedgerEntry] = []

    # ------------------------------------------------------------------
    # Vector lifecycle
    # ------------------------------------------------------------------
    def register_vector(
        self,
        name: str,
        *,
        glyph: str,
        amplitude: float = 1.0,
        metadata: Optional[Dict[str, object]] = None,
        narrative: str | None = None,
    ) -> FluxVector:
        """Register a new vector in the flux.

        Parameters
        ----------
        name:
            Unique identifier for the vector.
        glyph:
            Symbolic representation paired with the vector.
        amplitude:
            Initial amplitude baseline.  Defaults to ``1.0``.
        metadata:
            Optional arbitrary payload stored with the vector.
        narrative:
            Optional message recorded in the ledger to explain the
            registration.
        """

        if name in self._vectors:
            raise ValueError(f"vector {name!r} already registered")

        timestamp = self._time_source()
        vector = FluxVector(
            name=name,
            glyph=glyph,
            amplitude=amplitude,
            created_at=timestamp,
            updated_at=timestamp,
            metadata=dict(metadata or {}),
        )
        self._vectors[name] = vector
        self._append_ledger(
            timestamp=timestamp,
            vector=name,
            source="registry",
            delta=amplitude,
            narrative=narrative or "Vector registered",
        )
        return vector

    def infuse(
        self,
        name: str,
        *,
        source: str,
        delta: float,
        narrative: Optional[str] = None,
    ) -> FluxVector:
        """Inject additional resonance into a vector."""

        vector = self._require_vector(name)
        vector.contributions.append((source, delta))
        vector.updated_at = self._time_source()
        self._append_ledger(
            timestamp=vector.updated_at,
            vector=name,
            source=source,
            delta=delta,
            narrative=narrative or "Infusion applied",
        )
        return vector

    def stabilise(
        self,
        name: str,
        *,
        new_amplitude: float,
        narrative: Optional[str] = None,
    ) -> FluxVector:
        """Overwrite the baseline amplitude for a vector."""

        vector = self._require_vector(name)
        vector.amplitude = new_amplitude
        vector.updated_at = self._time_source()
        self._append_ledger(
            timestamp=vector.updated_at,
            vector=name,
            source="stabiliser",
            delta=new_amplitude,
            narrative=narrative or "Amplitude stabilised",
        )
        return vector

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------
    def orbital_signature(self) -> str:
        """Return a deterministic signature representing the current flux."""

        digest_input = [self.anchor]
        for name in sorted(self._vectors):
            vector = self._vectors[name]
            digest_input.append(f"{name}:{vector.glyph}:{vector.energy():.6f}")
        payload = "|".join(digest_input).encode("utf-8")
        return sha256(payload).hexdigest()

    def manifest(self, *, ledger_limit: Optional[int] = None) -> Dict[str, object]:
        """Return a serialisable snapshot of the flux state."""

        vectors = sorted(
            (vector.to_dict() for vector in self._vectors.values()),
            key=lambda entry: entry["energy"],
            reverse=True,
        )
        if ledger_limit is None:
            ledger_entries: Iterable[FluxLedgerEntry] = self._ledger
        else:
            ledger_entries = self._ledger[-ledger_limit:]
        return {
            "anchor": self.anchor,
            "signature": self.orbital_signature(),
            "vectors": vectors,
            "ledger": [entry.to_dict() for entry in ledger_entries],
        }

    def ledger_summary(self, *, by: str = "source") -> Dict[str, float]:
        """Aggregate ledger deltas grouped by ``source`` or ``vector``.

        The ledger often captures many small infusions from different
        collaborators.  ``ledger_summary`` helps callers understand the
        cumulative resonance from each contributor or vector without
        manually iterating over the ledger entries.

        Parameters
        ----------
        by:
            ``"source"`` (default) groups by the ledger entry ``source``
            while ``"vector"`` groups by the vector name.  Any other value
            raises :class:`ValueError` to guard against silent mistakes.
        """

        if by not in {"source", "vector"}:
            raise ValueError("ledger_summary can only group by 'source' or 'vector'")

        summary: Dict[str, float] = {}
        for entry in self._ledger:
            key = entry.source if by == "source" else entry.vector
            summary[key] = summary.get(key, 0.0) + entry.delta
        return summary

    def ledger(self) -> List[FluxLedgerEntry]:
        """Return a copy of the ledger entries."""

        return list(self._ledger)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _require_vector(self, name: str) -> FluxVector:
        try:
            return self._vectors[name]
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise KeyError(f"unknown vector {name!r}") from exc

    def _append_ledger(
        self,
        *,
        timestamp: datetime,
        vector: str,
        source: str,
        delta: float,
        narrative: str,
    ) -> None:
        entry = FluxLedgerEntry(
            timestamp=timestamp,
            vector=vector,
            source=source,
            delta=delta,
            narrative=narrative,
        )
        self._ledger.append(entry)

