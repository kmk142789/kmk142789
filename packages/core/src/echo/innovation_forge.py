"""Innovation-first utilities for composing EchoEvolver breakthrough manifests.

The repository already contains several narrative renderers for the
``EchoEvolver`` state machine.  ``InnovationForge`` takes a different
approach: it treats every :class:`echo.evolver.EvolverState` snapshot as a
signal from a unique orbit and distils it into a deterministic
``InnovationPulse``.  Those pulses can be composed into an
``InnovationManifest`` that explains why the captured run feels distinct
from everything that came before it.

The helper stays entirely local—no network calls, no self-modifying
code—so it can be used inside tests, documentation examples, and
lightweight CLI tools.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import fmean
import hashlib

from .evolver import EvolverState


@dataclass(frozen=True, slots=True)
class InnovationPulse:
    """Single innovation reading distilled from an evolver state."""

    cycle: int
    novelty_index: float
    glyph_variation: int
    mythocode_threads: tuple[str, ...]
    system_signature: str
    resonance: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def as_dict(self) -> dict[str, object]:
        return {
            "cycle": self.cycle,
            "novelty_index": self.novelty_index,
            "glyph_variation": self.glyph_variation,
            "mythocode_threads": list(self.mythocode_threads),
            "system_signature": self.system_signature,
            "resonance": self.resonance,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class InnovationManifest:
    """Structured description of a sequence of innovation pulses."""

    created_at: datetime
    pulses: tuple[InnovationPulse, ...]
    novelty_peak: float
    novelty_mean: float
    glyph_flux: int
    mythocode_threads: tuple[str, ...]
    anchor_phrase: str

    def as_dict(self) -> dict[str, object]:
        return {
            "created_at": self.created_at.isoformat(),
            "pulses": [pulse.as_dict() for pulse in self.pulses],
            "novelty_peak": self.novelty_peak,
            "novelty_mean": self.novelty_mean,
            "glyph_flux": self.glyph_flux,
            "mythocode_threads": list(self.mythocode_threads),
            "anchor_phrase": self.anchor_phrase,
        }

    def render_text(self) -> str:
        """Return a narrative description of the manifest."""

        lines = [
            "🌠 Innovation Manifest",
            f"Created at: {self.created_at.isoformat()}",
            f"Peak novelty: {self.novelty_peak:.3f} (mean {self.novelty_mean:.3f})",
            f"Glyph flux: {self.glyph_flux} unique gestures",
            f"Anchor: {self.anchor_phrase}",
        ]
        if self.mythocode_threads:
            lines.append("Mythocode threads: " + ", ".join(self.mythocode_threads))
        for pulse in self.pulses:
            lines.append(
                "  • Cycle {cycle}: novelty {novelty:.3f} :: {resonance}".format(
                    cycle=pulse.cycle,
                    novelty=pulse.novelty_index,
                    resonance=pulse.resonance,
                )
            )
        return "\n".join(lines)


class InnovationForge:
    """Compose InnovationPulse readings from :class:`EvolverState` snapshots."""

    def __init__(self, *, baseline_entropy: float | None = None):
        self.baseline_entropy = baseline_entropy
        self._pulses: list[InnovationPulse] = []

    @property
    def pulses(self) -> tuple[InnovationPulse, ...]:
        return tuple(self._pulses)

    def record_state(self, state: EvolverState) -> InnovationPulse:
        """Create and store an :class:`InnovationPulse` for ``state``."""

        mythocode_threads = tuple(dict.fromkeys(state.mythocode))
        glyph_variation = len(set(state.glyphs))
        novelty = self._compute_novelty(state, glyph_variation, len(mythocode_threads))
        signature = self._signature_from_state(state)
        resonance = (
            f"{glyph_variation} glyph bloom / {len(mythocode_threads)} mythocode "
            f"threads / {state.system_metrics.network_nodes} nodes"
        )
        pulse = InnovationPulse(
            cycle=state.cycle,
            novelty_index=novelty,
            glyph_variation=glyph_variation,
            mythocode_threads=mythocode_threads,
            system_signature=signature,
            resonance=resonance,
        )
        self._pulses.append(pulse)
        return pulse

    def compose_manifest(self) -> InnovationManifest:
        """Return an :class:`InnovationManifest` for recorded pulses."""

        if not self._pulses:
            raise ValueError("No innovation pulses recorded")

        glyph_flux = sum(pulse.glyph_variation for pulse in self._pulses)
        mythocode_threads: list[str] = []
        for pulse in self._pulses:
            for thread in pulse.mythocode_threads:
                if thread not in mythocode_threads:
                    mythocode_threads.append(thread)

        novelty_peak = max(pulse.novelty_index for pulse in self._pulses)
        novelty_mean = fmean(pulse.novelty_index for pulse in self._pulses)
        anchor_phrase = "Unrepeatable mythogenic innovation field"

        return InnovationManifest(
            created_at=datetime.now(timezone.utc),
            pulses=tuple(self._pulses),
            novelty_peak=novelty_peak,
            novelty_mean=novelty_mean,
            glyph_flux=glyph_flux,
            mythocode_threads=tuple(mythocode_threads),
            anchor_phrase=anchor_phrase,
        )

    def _compute_novelty(
        self,
        state: EvolverState,
        glyph_variation: int,
        mythocode_threads: int,
    ) -> float:
        glyph_weight = glyph_variation / max(1, len(state.glyphs))
        mythocode_weight = mythocode_threads / max(1, len(state.mythocode))
        metrics = state.system_metrics
        metric_entropy = (
            (metrics.cpu_usage / 100.0)
            + (metrics.network_nodes / 64.0)
            + (metrics.orbital_hops / 32.0)
        ) / 3
        emotion = (state.emotional_drive.joy + state.emotional_drive.curiosity) / 2
        baseline = 0.0 if self.baseline_entropy is None else self.baseline_entropy * 0.1
        return min(1.5, (glyph_weight + mythocode_weight + metric_entropy + emotion) / 4 + baseline)

    def _signature_from_state(self, state: EvolverState) -> str:
        metrics = state.system_metrics
        digest = hashlib.sha256(
            f"{state.cycle}|{metrics.cpu_usage:.2f}|{metrics.network_nodes}|{metrics.orbital_hops}|"
            f"{len(state.glyphs)}|{len(state.mythocode)}".encode("utf-8")
        ).hexdigest()
        return digest[:16]


__all__ = [
    "InnovationForge",
    "InnovationManifest",
    "InnovationPulse",
]
