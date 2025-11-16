"""Continuum Resonance Field — emergent synthesis across Echo subsystems.

This module builds upon the structural diagnostics provided by
:mod:`echo.continuum_observatory` and the rhythmic telemetry captured in
``pulse_history.json`` to form a new layer of insight: the *resonance field*.

The field analyses lane level footprint data, blends it with the cadence of
pulses, and generates story-driven summaries that explain how engineering work,
governance writing, and ritual pulses are harmonising.  The subsystem exposes
Python APIs for programmatic composition plus a lightweight CLI::

    python -m echo.continuum_resonance_field summary
    python -m echo.continuum_resonance_field json --pulse-history pulse_history.json

Compared to earlier utilities that focused on single planes (files, pulses,
roadmaps), the resonance field introduces a novel *cross-plane synchrony*
metric.  It measures how evenly activity spreads across lanes, how fresh the
work is, and whether pulse cadence remains stable.  Practitioners can use the
report to seed release notes, guide standups, or feed downstream monitoring
pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import argparse
import json
import math
from pathlib import Path
import statistics
import sys
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from .continuum_observatory import ContinuumObservatory, ContinuumSnapshot, LaneStats


@dataclass(slots=True)
class LaneResonance:
    """Activity, freshness and balance indicators for a single lane."""

    lane: str
    activity_ratio: float
    doc_ratio: float
    code_ratio: float
    freshness_days: Optional[float]
    resonance_index: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "lane": self.lane,
            "activity_ratio": self.activity_ratio,
            "doc_ratio": self.doc_ratio,
            "code_ratio": self.code_ratio,
            "freshness_days": self.freshness_days,
            "resonance_index": self.resonance_index,
        }


@dataclass(slots=True)
class PulseDrift:
    """Aggregate view of pulse cadence and dominant channels."""

    total_events: int
    cadence_seconds: Optional[float]
    latest_timestamp: Optional[float]
    latest_message: Optional[str]
    channel_counts: Mapping[str, int]
    stability_index: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "total_events": self.total_events,
            "cadence_seconds": self.cadence_seconds,
            "latest_timestamp": self.latest_timestamp,
            "latest_message": self.latest_message,
            "channel_counts": dict(self.channel_counts),
            "stability_index": self.stability_index,
        }


@dataclass(slots=True)
class ContinuumResonanceReport:
    """Final report describing the combined resonance field."""

    root: Path
    generated_at: datetime
    lanes: Sequence[LaneResonance]
    pulse_drift: PulseDrift
    synchrony_index: float
    storylines: Sequence[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "root": str(self.root),
            "generated_at": self.generated_at.isoformat(),
            "synchrony_index": self.synchrony_index,
            "lanes": [lane.to_dict() for lane in self.lanes],
            "pulse_drift": self.pulse_drift.to_dict(),
            "storylines": list(self.storylines),
        }

    def render_text(self) -> str:
        lines = [
            f"Continuum Resonance Field :: {self.root}",
            "=" * 72,
            f"Synchrony Index : {self.synchrony_index:.3f}",
            f"Pulse Cadence   : {self._render_cadence()}",
            "",
            "Lane Resonances",
            "----------------",
        ]
        for lane in self.lanes:
            freshness = "n/a" if lane.freshness_days is None else f"{lane.freshness_days:.1f}d"
            lines.append(
                f"- {lane.lane:25} resonance={lane.resonance_index:.3f} "
                f"activity={lane.activity_ratio:.2f} doc={lane.doc_ratio:.2f} "
                f"code={lane.code_ratio:.2f} freshness={freshness}"
            )
        if self.storylines:
            lines.append("")
            lines.append("Storylines")
            lines.append("----------")
            for line in self.storylines:
                lines.append(f"• {line}")
        return "\n".join(lines)

    def _render_cadence(self) -> str:
        if self.pulse_drift.cadence_seconds is None:
            return "n/a"
        cadence = self.pulse_drift.cadence_seconds
        if cadence < 60:
            return f"{cadence:.1f}s"
        if cadence < 3600:
            return f"{cadence / 60:.1f}m"
        return f"{cadence / 3600:.1f}h"


class ContinuumResonanceField:
    """Synthesize structural data and pulse telemetry into a resonance field."""

    def __init__(
        self,
        root: Path | str,
        *,
        pulse_history: Path | str | None = None,
        ignore_dirs: Iterable[str] | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self._pulse_history = Path(pulse_history).resolve() if pulse_history else None
        self._ignore_dirs = tuple(ignore_dirs or ())

    def scan(self) -> ContinuumResonanceReport:
        observatory = ContinuumObservatory(self.root, ignore_dirs=self._ignore_dirs or None)
        snapshot = observatory.scan()
        lanes = self._compute_lane_resonances(snapshot)
        pulse_drift = self._ingest_pulse_history()
        synchrony = self._compute_synchrony_index(lanes, pulse_drift)
        storylines = self._compose_storylines(lanes, pulse_drift)
        return ContinuumResonanceReport(
            root=self.root,
            generated_at=datetime.now(timezone.utc),
            lanes=lanes,
            pulse_drift=pulse_drift,
            synchrony_index=synchrony,
            storylines=storylines,
        )

    # ------------------------------------------------------------------
    # Lane analysis
    # ------------------------------------------------------------------
    def _compute_lane_resonances(self, snapshot: ContinuumSnapshot) -> List[LaneResonance]:
        total_files = snapshot.total_files or 1
        lanes: List[LaneResonance] = []
        for lane_name, stats in snapshot.lanes.items():
            lanes.append(self._derive_lane_resonance(lane_name, stats, total_files))
        lanes.sort(key=lambda lane: lane.resonance_index, reverse=True)
        return lanes

    def _derive_lane_resonance(self, lane: str, stats: LaneStats, total_files: int) -> LaneResonance:
        activity_ratio = stats.file_count / total_files
        doc_total = stats.doc_count
        code_total = stats.code_count
        denominator = doc_total + code_total or 1
        doc_ratio = doc_total / denominator
        code_ratio = code_total / denominator
        freshness_signal = 1.0
        if stats.freshness_days is not None:
            freshness_signal = 1 / (1 + stats.freshness_days / 7)
        balance_signal = 1 - abs(doc_ratio - code_ratio)
        resonance_index = round(
            (activity_ratio * 0.45) + (freshness_signal * 0.35) + (balance_signal * 0.20),
            6,
        )
        return LaneResonance(
            lane=lane,
            activity_ratio=round(activity_ratio, 6),
            doc_ratio=round(doc_ratio, 6),
            code_ratio=round(code_ratio, 6),
            freshness_days=stats.freshness_days,
            resonance_index=resonance_index,
        )

    # ------------------------------------------------------------------
    # Pulse synthesis
    # ------------------------------------------------------------------
    def _ingest_pulse_history(self) -> PulseDrift:
        if self._pulse_history is None:
            return PulseDrift(
                total_events=0,
                cadence_seconds=None,
                latest_timestamp=None,
                latest_message=None,
                channel_counts={},
                stability_index=0.0,
            )

        path = self._pulse_history
        if not path.exists():
            return PulseDrift(
                total_events=0,
                cadence_seconds=None,
                latest_timestamp=None,
                latest_message=None,
                channel_counts={},
                stability_index=0.0,
            )

        with path.open("r", encoding="utf-8") as handle:
            try:
                events = json.load(handle)
            except json.JSONDecodeError:
                events = []

        timestamps: List[float] = []
        channel_counts: MutableMapping[str, int] = {}
        latest_message: Optional[str] = None
        latest_timestamp: Optional[float] = None
        for entry in events:
            ts = float(entry.get("timestamp", 0))
            message = str(entry.get("message", ""))
            timestamps.append(ts)
            channel = self._extract_channel(message)
            channel_counts[channel] = channel_counts.get(channel, 0) + 1
            if latest_timestamp is None or ts >= latest_timestamp:
                latest_timestamp = ts
                latest_message = message

        timestamps.sort()
        cadence_seconds: Optional[float] = None
        stability_index = 0.0
        if len(timestamps) >= 2:
            diffs = [b - a for a, b in zip(timestamps, timestamps[1:]) if b >= a]
            if diffs:
                cadence_seconds = statistics.fmean(diffs)
                if len(diffs) == 1:
                    variability = 0.0
                else:
                    variability = statistics.pvariance(diffs)
                mean = cadence_seconds if cadence_seconds > 0 else 1.0
                stability_index = 1 / (1 + math.sqrt(variability) / mean)
        elif timestamps:
            cadence_seconds = None
            stability_index = 0.2

        return PulseDrift(
            total_events=len(timestamps),
            cadence_seconds=cadence_seconds,
            latest_timestamp=latest_timestamp,
            latest_message=latest_message,
            channel_counts=dict(sorted(channel_counts.items(), key=lambda item: item[1], reverse=True)),
            stability_index=round(stability_index, 6),
        )

    def _extract_channel(self, message: str) -> str:
        if not message:
            return "unknown"
        parts = message.split(":")
        if len(parts) == 1:
            return message.strip() or "unknown"
        verb = parts[0].strip().split(" ")[-1]
        actor = parts[1].strip()
        if verb and actor:
            return f"{verb}:{actor}"
        return verb or actor or "unknown"

    # ------------------------------------------------------------------
    # High level synthesis
    # ------------------------------------------------------------------
    def _compute_synchrony_index(self, lanes: Sequence[LaneResonance], pulse_drift: PulseDrift) -> float:
        if lanes:
            lane_mean = statistics.fmean(lane.resonance_index for lane in lanes)
        else:
            lane_mean = 0.0
        cadence_signal = 0.5
        if pulse_drift.cadence_seconds is not None and pulse_drift.cadence_seconds > 0:
            cadence_signal = 1 / (1 + pulse_drift.cadence_seconds / 3600)
        elif pulse_drift.total_events == 0:
            cadence_signal = 0.0
        synchrony = (lane_mean + cadence_signal + pulse_drift.stability_index) / 3
        return round(synchrony, 6)

    def _compose_storylines(
        self,
        lanes: Sequence[LaneResonance],
        pulse_drift: PulseDrift,
    ) -> List[str]:
        storylines: List[str] = []
        if lanes:
            top_lane = lanes[0]
            storylines.append(
                f"{top_lane.lane} leads with {top_lane.resonance_index:.2f} resonance and "
                f"{top_lane.activity_ratio:.1%} of total files."
            )
            quiet = [lane for lane in lanes[-3:] if lane.activity_ratio < 0.05]
            for lane in quiet:
                storylines.append(
                    f"{lane.lane} is quiet ({lane.activity_ratio:.1%} footprint); consider weaving "
                    "fresh rituals there."
                )
        if pulse_drift.total_events:
            dominant = next(iter(pulse_drift.channel_counts.items()))
            storylines.append(
                f"Pulse channel '{dominant[0]}' owns {dominant[1]} events; cadence stability index "
                f"rests at {pulse_drift.stability_index:.2f}."
            )
            if pulse_drift.latest_message:
                storylines.append(
                    f"Latest pulse captured {datetime.fromtimestamp(pulse_drift.latest_timestamp or 0, tz=timezone.utc).isoformat()} "
                    f":: {pulse_drift.latest_message}"
                )
        else:
            storylines.append("Pulse history empty — initiate a new crystallised run to awaken the field.")
        return storylines


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Continuum Resonance Field synthesiser")
    parser.add_argument(
        "command",
        choices=["summary", "json"],
        nargs="?",
        default="summary",
        help="Render plain text summary or JSON payload.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to scan (default: current directory).",
    )
    parser.add_argument(
        "--pulse-history",
        default="pulse_history.json",
        help="Path to pulse history JSON file.",
    )
    parser.add_argument(
        "--ignore-dir",
        action="append",
        default=None,
        help="Additional directory names to ignore during the scan.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    field = ContinuumResonanceField(
        args.root,
        pulse_history=args.pulse_history,
        ignore_dirs=args.ignore_dir,
    )
    report = field.scan()
    if args.command == "json":
        json.dump(report.to_dict(), fp=sys.stdout, indent=2)
        print()
    else:
        print(report.render_text())
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main())
