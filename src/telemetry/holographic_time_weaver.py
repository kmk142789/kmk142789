"""Holographic telemetry weaver that braids short- and long-horizon signals.

This module introduces a "temporal hologram" representation for telemetry data.
It is designed as a world-first fusion of:
- tri-horizon windows (heartbeat, narrative, and epochal spans),
- braid lines that keep a human-auditable trace of the latest pulses, and
- an "entanglement index" that scores how surprising and well-distributed events
  are across time and type.

The result is a concise frame that can be exported, streamed, or
post-processed without leaking sensitive payload details.
"""

from __future__ import annotations

import hashlib
import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Sequence

from .schema import TelemetryEvent


@dataclass(frozen=True, slots=True)
class HologramFrame:
    """A single holographic snapshot of telemetry activity."""

    horizon_seconds: int
    event_count: int
    event_types: dict[str, int]
    entanglement_index: float
    flux_signature: str
    braid: list[str]

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-friendly representation of the frame."""

        return {
            "horizon_seconds": self.horizon_seconds,
            "event_count": self.event_count,
            "event_types": dict(self.event_types),
            "entanglement_index": self.entanglement_index,
            "flux_signature": self.flux_signature,
            "braid": list(self.braid),
        }


class TemporalHologramWeaver:
    """Constructs hologram frames from telemetry events.

    The weaver intentionally spans three horizons:
    - a heartbeat horizon for near-real-time reflections,
    - a narrative horizon that captures session-length arcs,
    - and an epochal horizon for longer-running patterns.

    Each frame combines distribution-aware scoring with a privacy-preserving
    flux signature that compresses payload fingerprints without storing any
    raw user data.
    """

    def __init__(
        self,
        *,
        horizons: Sequence[int] = (21, 233, 1447),
        braid_width: int = 7,
    ) -> None:
        self.horizons = tuple(int(h) for h in horizons)
        self.braid_width = braid_width

    def weave(self, events: Iterable[TelemetryEvent]) -> list[HologramFrame]:
        """Weave hologram frames across configured horizons."""

        prepared = list(events)
        now = datetime.now(timezone.utc)
        frames: list[HologramFrame] = []

        for horizon in self.horizons:
            window_start = now - timedelta(seconds=horizon)
            window_events = [
                event
                for event in prepared
                if event.occurred_at is not None
                and event.occurred_at.replace(tzinfo=timezone.utc) >= window_start
            ]

            if not window_events:
                frames.append(
                    HologramFrame(
                        horizon_seconds=horizon,
                        event_count=0,
                        event_types={},
                        entanglement_index=0.0,
                        flux_signature=self._empty_signature(horizon),
                        braid=[],
                    )
                )
                continue

            event_types = self._type_counts(window_events)
            entanglement = self._entanglement_index(window_events, event_types)
            flux_signature = self._flux_signature(
                horizon=horizon,
                events=window_events,
                entanglement=entanglement,
                event_types=event_types,
            )
            braid = self._braid(window_events)

            frames.append(
                HologramFrame(
                    horizon_seconds=horizon,
                    event_count=len(window_events),
                    event_types=event_types,
                    entanglement_index=entanglement,
                    flux_signature=flux_signature,
                    braid=braid,
                )
            )

        return frames

    def weave_from_storage(self, storage) -> list[HologramFrame]:
        """Convenience wrapper to weave frames from a TelemetryStorage backend."""

        return self.weave(storage.read())

    def _type_counts(self, events: Iterable[TelemetryEvent]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in events:
            counts[event.event_type] = counts.get(event.event_type, 0) + 1
        return counts

    def _entanglement_index(
        self, events: Sequence[TelemetryEvent], event_types: dict[str, int]
    ) -> float:
        """Blend temporal spacing and type diversity into a single score."""

        occurrences = sorted(e.occurred_at.timestamp() for e in events)
        gaps = [b - a for a, b in zip(occurrences, occurrences[1:])]
        if not gaps:
            return 1.0 + math.tanh(len(event_types))

        gap_mean = statistics.fmean(gaps)
        gap_variation = statistics.pstdev(gaps) if len(gaps) > 1 else 0.0
        diversity = len(event_types)

        # Encourage both spacing stability and type diversity.
        baseline = math.tanh(diversity) + 1.0
        stability = 1 / (1 + gap_variation)
        rhythm = math.exp(-abs(gap_mean - gap_variation) / max(gap_mean, 0.01))

        return round(baseline * stability * (1 + rhythm), 4)

    def _flux_signature(
        self,
        *,
        horizon: int,
        events: Sequence[TelemetryEvent],
        entanglement: float,
        event_types: dict[str, int],
    ) -> str:
        """Generate a privacy-preserving digest describing the hologram."""

        digest = hashlib.sha3_256()
        digest.update(str(horizon).encode("utf-8"))
        digest.update(str(len(events)).encode("utf-8"))
        digest.update(str(round(entanglement, 4)).encode("utf-8"))

        for event_type, count in sorted(event_types.items()):
            digest.update(f"{event_type}:{count}".encode("utf-8"))

        for event in events[-self.braid_width :]:
            # Only use structural hints from payload keys to avoid sensitive data.
            payload_keys = ",".join(sorted(event.payload.keys()))
            digest.update(payload_keys.encode("utf-8"))
            digest.update(event.context.consent_state.value.encode("utf-8"))
            label_hint = event.context.session_label or event.context.pseudonymous_id[:8]
            digest.update(label_hint.encode("utf-8"))

        return f"HX-{digest.hexdigest()[:18]}"

    def _braid(self, events: Sequence[TelemetryEvent]) -> list[str]:
        """Create a compact, human-auditable braid of recent pulses."""

        braid_lines: list[str] = []
        for event in events[-self.braid_width :]:
            label_hint = event.context.session_label or event.context.pseudonymous_id[:8]
            glyph = self._payload_glyph(event.payload)
            braid_lines.append(f"{event.event_type}@{label_hint}:{glyph}")
        return braid_lines

    def _payload_glyph(self, payload: dict[str, object]) -> str:
        """Summarise a payload using structural glyphs instead of raw data."""

        if not payload:
            return "∅"
        glyphs: list[str] = []
        for key in sorted(payload.keys()):
            length = len(str(payload[key]))
            glyphs.append(f"{key[:4]}:{length}")
        return "|".join(glyphs)

    def _empty_signature(self, horizon: int) -> str:
        return f"HX-empty-{horizon}"


__all__ = ["HologramFrame", "TemporalHologramWeaver"]
