"""Orbital resonance analytics for EchoEvolver cycles.

This module ingests one or more persisted EchoEvolver cycle payloads and
derives higher-order metrics that are not recorded by the base engine.
Unlike the interactive, narrative-heavy ``EchoEvolver`` runtime, the
``OrbitalResonanceAnalyzer`` focuses on quantifiable signals:

* glyph density, entropy, and lattice distribution
* emotional flux between sequential cycles
* quantam alignment and coherence windows
* orbital stability projections informed by resource metrics

The analyzer is deliberately deterministic.  Every derived metric is based
solely on the provided payloads so that automated systems can compare
results across code revisions without relying on ambient state or network
access.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
import math
from pathlib import Path
import statistics
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _round(value: float, digits: int = 6) -> float:
    return round(value, digits)


@dataclass(frozen=True)
class CycleSnapshot:
    """Immutable projection of a single EchoEvolver cycle payload."""

    cycle: int
    glyphs: str
    glyph_vortex: str | None
    emotional_drive: Mapping[str, float]
    system_metrics: Mapping[str, float | int]
    quantam_ability: Mapping[str, object]
    quantam_capability: Mapping[str, object]

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "CycleSnapshot":
        glyphs = str(payload.get("glyphs", ""))
        return cls(
            cycle=int(payload.get("cycle", 0)),
            glyphs=glyphs,
            glyph_vortex=payload.get("glyph_vortex"),
            emotional_drive=dict(payload.get("emotional_drive", {})),
            system_metrics=dict(payload.get("system_metrics", {})),
            quantam_ability=dict(payload.get("quantam_ability", {})),
            quantam_capability=dict(payload.get("quantam_capability", {})),
        )

    @property
    def joy(self) -> float:
        return _as_float(self.emotional_drive.get("joy"))

    @property
    def curiosity(self) -> float:
        return _as_float(self.emotional_drive.get("curiosity"))

    @property
    def rage(self) -> float:
        return _as_float(self.emotional_drive.get("rage"))

    @property
    def glyph_count(self) -> int:
        return len(self.glyphs)

    @property
    def entanglement(self) -> float:
        return _as_float(self.quantam_capability.get("entanglement"))

    @property
    def lattice_spin(self) -> float:
        return _as_float(self.quantam_ability.get("lattice_spin"))

    @property
    def glyph_flux(self) -> float:
        return _as_float(self.quantam_capability.get("glyph_flux"))

    def system_value(self, key: str, default: float = 0.0) -> float:
        return _as_float(self.system_metrics.get(key), default)


class OrbitalResonanceAnalyzer:
    """Derive orbital analytics from EchoEvolver cycle payloads."""

    def __init__(self, snapshots: Sequence[CycleSnapshot], smoothing_window: int = 3):
        if not snapshots:
            raise ValueError("snapshots must not be empty")
        self.snapshots: List[CycleSnapshot] = sorted(snapshots, key=lambda s: s.cycle)
        self.smoothing_window = max(1, smoothing_window)
        self._cache: MutableMapping[str, object] = {}

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_payloads(
        cls, payloads: Iterable[Mapping[str, object]], smoothing_window: int = 3
    ) -> "OrbitalResonanceAnalyzer":
        snapshots = [CycleSnapshot.from_payload(payload) for payload in payloads]
        if not snapshots:
            raise ValueError("payloads must contain at least one entry")
        return cls(snapshots, smoothing_window=smoothing_window)

    @classmethod
    def from_artifact(
        cls, path: Path | str, smoothing_window: int = 3
    ) -> "OrbitalResonanceAnalyzer":
        payloads = load_payloads_from_artifact(path)
        return cls.from_payloads(payloads, smoothing_window=smoothing_window)

    # ------------------------------------------------------------------
    # Glyph analytics
    # ------------------------------------------------------------------
    def glyph_histogram(self) -> Mapping[str, int]:
        cached = self._cache.get("glyph_histogram")
        if cached is not None:
            return cached  # type: ignore[return-value]

        histogram: Counter[str] = Counter()
        for snapshot in self.snapshots:
            histogram.update(snapshot.glyphs)

        self._cache["glyph_histogram"] = histogram
        return histogram

    def glyph_entropy(self) -> float:
        cached = self._cache.get("glyph_entropy")
        if cached is not None:
            return cached  # type: ignore[return-value]

        histogram = self.glyph_histogram()
        total = sum(histogram.values())
        if total == 0:
            return 0.0

        entropy = 0.0
        for count in histogram.values():
            probability = count / total
            entropy -= probability * math.log2(probability)

        value = _round(entropy, 6)
        self._cache["glyph_entropy"] = value
        return value

    def glyph_density_index(self) -> float:
        cached = self._cache.get("glyph_density")
        if cached is not None:
            return cached  # type: ignore[return-value]

        densities: List[float] = []
        for snapshot in self.snapshots:
            baseline = snapshot.cycle if snapshot.cycle > 0 else 1
            densities.append(snapshot.glyph_count / baseline)

        density = statistics.fmean(densities)
        value = _round(density, 6)
        self._cache["glyph_density"] = value
        return value

    # ------------------------------------------------------------------
    # Emotional analytics
    # ------------------------------------------------------------------
    def emotional_flux(self) -> List[Dict[str, float]]:
        cached = self._cache.get("emotional_flux")
        if cached is not None:
            return cached  # type: ignore[return-value]

        flux: List[Dict[str, float]] = []
        for previous, current in zip(self.snapshots, self.snapshots[1:]):
            flux.append(
                {
                    "cycle": float(current.cycle),
                    "joy_delta": _round(current.joy - previous.joy, 6),
                    "curiosity_delta": _round(
                        current.curiosity - previous.curiosity, 6
                    ),
                    "rage_delta": _round(current.rage - previous.rage, 6),
                }
            )

        self._cache["emotional_flux"] = flux
        return flux

    def smoothed_emotional_baseline(self, window: int | None = None) -> List[Dict[str, float]]:
        """Rolling averages for emotional drives using a configurable window.

        The analyzer accepts a ``smoothing_window`` during construction; callers can
        override it on a per-call basis by providing ``window``.  Values are
        averaged over the most recent ``window`` snapshots so shorter histories do
        not dilute early cycles.
        """

        size = max(1, window or self.smoothing_window)
        cache_key = f"smoothed_emotional_baseline/{size}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        baseline: List[Dict[str, float]] = []
        for index, snapshot in enumerate(self.snapshots):
            start = max(0, index - size + 1)
            window_snapshots = self.snapshots[start : index + 1]
            baseline.append(
                {
                    "cycle": float(snapshot.cycle),
                    "joy_avg": _round(statistics.fmean(s.joy for s in window_snapshots)),
                    "curiosity_avg": _round(
                        statistics.fmean(s.curiosity for s in window_snapshots)
                    ),
                    "rage_avg": _round(statistics.fmean(s.rage for s in window_snapshots)),
                }
            )

        self._cache[cache_key] = baseline
        return baseline

    def detect_resonance_bursts(self, threshold: float = 0.07) -> List[Dict[str, float]]:
        bursts: List[Dict[str, float]] = []
        for entry in self.emotional_flux():
            magnitude = math.sqrt(
                entry["joy_delta"] ** 2
                + entry["curiosity_delta"] ** 2
                + entry["rage_delta"] ** 2
            )
            if magnitude >= threshold:
                enriched = dict(entry)
                enriched["magnitude"] = _round(magnitude, 6)
                bursts.append(enriched)
        return bursts

    # ------------------------------------------------------------------
    # Orbital / quantam analytics
    # ------------------------------------------------------------------
    def stability_band(self) -> str:
        nodes = statistics.fmean(s.system_value("network_nodes") for s in self.snapshots)
        hops = statistics.fmean(s.system_value("orbital_hops") for s in self.snapshots)
        cpu = statistics.fmean(s.system_value("cpu_usage") for s in self.snapshots)

        if hops >= 4.5 and nodes >= 12 and cpu <= 40:
            return "orbital-high"
        if hops >= 3.0 and nodes >= 9:
            return "orbital-stable"
        return "orbital-fragile"

    def quantam_alignment(self) -> Dict[str, float]:
        entanglement = statistics.fmean(s.entanglement for s in self.snapshots)
        lattice_spin = statistics.fmean(s.lattice_spin for s in self.snapshots)
        glyph_flux = statistics.fmean(s.glyph_flux for s in self.snapshots)
        return {
            "entanglement": _round(entanglement, 6),
            "lattice_spin": _round(lattice_spin, 6),
            "glyph_flux": _round(glyph_flux, 6),
        }

    def resonance_index(self) -> float:
        entropy = self.glyph_entropy()
        density = self.glyph_density_index()
        alignment = self.quantam_alignment()
        entanglement = alignment["entanglement"]
        spin = alignment["lattice_spin"]
        index = entropy * 0.4 + density * 0.3 + entanglement * 0.2 + spin * 0.1
        return _round(index, 6)

    def momentum_index(self) -> float:
        """Aggregate intensity of emotional swings across observed cycles.

        The metric is the mean magnitude of the Euclidean deltas recorded by
        :meth:`emotional_flux`.  A value near zero reflects smooth evolution,
        while higher magnitudes highlight volatile transitions between cycles.
        """

        flux = self.emotional_flux()
        if not flux:
            return 0.0

        magnitudes = [
            math.sqrt(
                entry["joy_delta"] ** 2
                + entry["curiosity_delta"] ** 2
                + entry["rage_delta"] ** 2
            )
            for entry in flux
        ]
        return _round(statistics.fmean(magnitudes), 6)

    def projection(self) -> Dict[str, float]:
        if len(self.snapshots) == 1:
            snapshot = self.snapshots[0]
            return {
                "cycle": float(snapshot.cycle + 1),
                "joy": snapshot.joy,
                "curiosity": snapshot.curiosity,
                "rage": snapshot.rage,
            }

        last_snapshot = self.snapshots[-1]
        last_flux = self.emotional_flux()[-1]
        projection = {
            "cycle": float(last_snapshot.cycle + 1),
            "joy": _round(max(0.0, min(1.0, last_snapshot.joy + last_flux["joy_delta"])), 6),
            "curiosity": _round(
                max(0.0, min(1.0, last_snapshot.curiosity + last_flux["curiosity_delta"])), 6
            ),
            "rage": _round(
                max(0.0, min(1.0, last_snapshot.rage + last_flux["rage_delta"])), 6
            ),
        }
        return projection

    # ------------------------------------------------------------------
    # High level summary
    # ------------------------------------------------------------------
    def summary(self) -> Dict[str, object]:
        glyph_histogram = self.glyph_histogram()
        summary: Dict[str, object] = {
            "cycles_analyzed": len(self.snapshots),
            "cycle_range": {
                "start": self.snapshots[0].cycle,
                "end": self.snapshots[-1].cycle,
            },
            "glyph_entropy": self.glyph_entropy(),
            "glyph_density_index": self.glyph_density_index(),
            "glyph_histogram": dict(glyph_histogram),
            "emotional_flux": self.emotional_flux(),
            "emotional_baseline": self.smoothed_emotional_baseline(),
            "resonance_events": self.detect_resonance_bursts(),
            "stability_band": self.stability_band(),
            "quantam_alignment": self.quantam_alignment(),
            "resonance_index": self.resonance_index(),
            "momentum_index": self.momentum_index(),
            "projection": self.projection(),
        }
        return summary


def load_payloads_from_artifact(path: Path | str) -> List[Mapping[str, object]]:
    """Load one or more cycle payloads from ``path``.

    The loader accepts three formats:

    1. a JSON list containing fully detailed cycle payloads
    2. a JSON object with a ``"history"`` list attribute
    3. a single cycle payload stored as a JSON object
    """

    artifact_path = Path(path)
    raw = artifact_path.read_text(encoding="utf-8")
    data = json.loads(raw)

    if isinstance(data, list):
        return [dict(entry) for entry in data]

    if isinstance(data, dict):
        history = data.get("history")
        if isinstance(history, list) and history:
            return [dict(entry) for entry in history]
        return [dict(data)]

    raise TypeError(f"Unsupported artifact structure: {artifact_path}")


__all__ = [
    "CycleSnapshot",
    "OrbitalResonanceAnalyzer",
    "load_payloads_from_artifact",
]

