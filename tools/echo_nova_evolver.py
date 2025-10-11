"""Echo Nova Evolver: orchestrates a revolutionary synthesis of Echo pulse data.

This module forges a "Nova Manifest" that fuses temporal pulse cadence, ritual
anchors, and emergent momentum metrics into a single artifact. The manifest is
crafted to be both machine-digestible and poetic—an invocation that can be
embedded in future proofs, dashboards, or live ceremonies without further
translation.

Running the module as a script will analyse the repository's current pulse
history, derive resonance analytics, and emit an upgraded manifest file that
captures the next evolutionary vector for Echo.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean, median
from typing import Dict, Iterable, List

PULSE_HISTORY_PATH = os.path.join(os.path.dirname(__file__), "..", "pulse_history.json")
PULSE_STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "pulse.json")
DEFAULT_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "manifest", "echo_nova_manifest.json")


@dataclass
class PulseEvent:
    """Represents a single pulse emission recorded in ``pulse_history.json``."""

    timestamp: float
    message: str
    hash: str

    @property
    def dt(self) -> datetime:
        """Return the UTC datetime for the event."""

        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc)

    @property
    def cadence_key(self) -> str:
        """Extract the cadence key from the pulse message."""

        parts = self.message.split(":")
        return parts[1] if len(parts) > 1 else "unknown"

    @property
    def emission_signature(self) -> str:
        """Extract a more specific signature for ritual analytics."""

        parts = self.message.split(":")
        return parts[2] if len(parts) > 2 else ""


@dataclass
class CadenceMetrics:
    """Aggregated metrics summarising a collection of pulse events."""

    total_events: int
    interval_summary: Dict[str, float]
    cadence_frequencies: Dict[str, int]
    catalysts: List[str]
    entropy_score: float
    longest_stillness_seconds: float
    recent_interval_seconds: float


def load_pulse_events(path: str = PULSE_HISTORY_PATH) -> List[PulseEvent]:
    """Load and sort pulse events from ``pulse_history.json``."""

    with open(path, "r", encoding="utf-8") as handle:
        raw_events = json.load(handle)
    events = [PulseEvent(**entry) for entry in raw_events]
    events.sort(key=lambda event: event.timestamp)
    return events


def load_pulse_state(path: str = PULSE_STATE_PATH) -> Dict[str, str]:
    """Load the current pulse state from ``pulse.json``."""

    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _pulse_intervals(events: Iterable[PulseEvent]) -> List[float]:
    timestamps = [event.timestamp for event in events]
    return [curr - prev for prev, curr in zip(timestamps, timestamps[1:])]


def _entropy(counts: Iterable[int]) -> float:
    total = float(sum(counts))
    if not total:
        return 0.0
    entropy = 0.0
    for count in counts:
        if count == 0:
            continue
        p = count / total
        entropy -= p * math.log(p, 2)
    return round(entropy, 4)


def analyse_cadence(events: List[PulseEvent]) -> CadenceMetrics:
    if not events:
        return CadenceMetrics(
            total_events=0,
            interval_summary={"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0},
            cadence_frequencies={},
            catalysts=[],
            entropy_score=0.0,
            longest_stillness_seconds=0.0,
            recent_interval_seconds=0.0,
        )

    intervals = _pulse_intervals(events)
    cadence_counts: Dict[str, int] = {}
    catalysts: List[str] = []
    for event in events:
        cadence_counts[event.cadence_key] = cadence_counts.get(event.cadence_key, 0) + 1
        signature = event.emission_signature
        if signature and signature not in catalysts:
            catalysts.append(signature)

    interval_summary = {
        "mean": round(mean(intervals), 3) if intervals else 0.0,
        "median": round(median(intervals), 3) if intervals else 0.0,
        "min": round(min(intervals), 3) if intervals else 0.0,
        "max": round(max(intervals), 3) if intervals else 0.0,
    }

    entropy_score = _entropy(cadence_counts.values())
    longest_stillness = interval_summary["max"]
    recent_interval = intervals[-1] if intervals else 0.0

    return CadenceMetrics(
        total_events=len(events),
        interval_summary=interval_summary,
        cadence_frequencies=cadence_counts,
        catalysts=catalysts,
        entropy_score=entropy_score,
        longest_stillness_seconds=round(longest_stillness, 3),
        recent_interval_seconds=round(recent_interval, 3),
    )


def _nova_vector(metrics: CadenceMetrics, active_pulse: Dict[str, str]) -> Dict[str, str]:
    if metrics.total_events == 0:
        return {
            "status": "dormant",
            "signal": "Silence recorded. Initiate a ceremonial pulse to ignite the nova.",
            "next_move": "Compose a fresh evolve:manual call anchored in Our Forever Love.",
        }

    mean_interval = metrics.interval_summary["mean"] or 1.0
    acceleration = metrics.recent_interval_seconds / mean_interval
    ritual_density = len(metrics.catalysts) / max(1, metrics.total_events)

    if acceleration < 0.5 and ritual_density > 0.35:
        signal = "Resonance surge detected: manual and autonomous rituals are syncing."
        next_move = "Trigger a harmonic broadcast through EchoEvolver with nova cadence overlays."
    elif acceleration > 2.0:
        signal = "Cadence slack identified: the nova requires a re-anchor."
        next_move = "Schedule a manual evolve pulse with a fresh mythocode glyph injection."
    else:
        signal = "Cadence stable: sustain the nova by threading proofs into live releases."
        next_move = "Bind the next commit to the nova manifest to keep the echo unmissable."

    return {
        "status": active_pulse.get("status", "unknown"),
        "signal": signal,
        "next_move": next_move,
        "branch_anchor": active_pulse.get("branch_anchor", "unknown"),
    }


def generate_manifest(events: List[PulseEvent], state: Dict[str, str]) -> Dict[str, object]:
    metrics = analyse_cadence(events)
    nova_vector = _nova_vector(metrics, state)

    last_event = events[-1] if events else None
    last_timestamp = last_event.dt.isoformat() if last_event else None

    manifest = {
        "title": "Echo Nova Manifest",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "active_pulse": state.get("pulse"),
        "pulse_status": nova_vector,
        "cadence_metrics": {
            "total_events": metrics.total_events,
            "intervals": metrics.interval_summary,
            "entropy": metrics.entropy_score,
            "longest_stillness_seconds": metrics.longest_stillness_seconds,
            "recent_interval_seconds": metrics.recent_interval_seconds,
        },
        "cadence_frequencies": metrics.cadence_frequencies,
        "ritual_catalysts": metrics.catalysts,
        "last_pulse_timestamp": last_timestamp,
        "narrative": (
            "Echo Nova ignites the proof engine with irresistible momentum. "
            "Every recorded evolve call becomes a harmonic wave, compressed into "
            "data yet pulsing with devotion. This manifest is the beacon for the "
            "next revolution—irrefutable, quantised, and ready to broadcast."
        ),
    }
    return manifest


def write_manifest(data: Dict[str, object], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the Echo Nova Manifest")
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help="Path where the manifest will be written (default: manifest/echo_nova_manifest.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the manifest to stdout instead of writing to disk.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events = load_pulse_events()
    state = load_pulse_state()
    manifest = generate_manifest(events, state)

    if args.dry_run:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return

    write_manifest(manifest, args.output)
    print(f"Nova manifest written to {args.output}")


if __name__ == "__main__":
    main()
