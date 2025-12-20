"""Continuum snapshot synthesiser for Echo operations.

This module merges wish, pulse, and plan signals into a single report so
operators can grab a quick holistic view without running multiple commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from .continuum_health import ContinuumHealthReport, generate_continuum_health
from .continuum_observatory import ContinuumObservatory, ContinuumSnapshot, LaneStats
from .echo_codox_kernel import EchoCodexKernel, PulseEvent
from .pulse_health import PulseLedgerMetrics, compute_pulse_metrics
from .wish_insights import summarize_wishes


@dataclass(slots=True)
class WishSnapshot:
    total: int
    unique_wishers: int
    statuses: dict[str, int]
    top_catalysts: List[tuple[str, int]]
    latest: Optional[dict[str, str]]

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "unique_wishers": self.unique_wishers,
            "statuses": dict(self.statuses),
            "top_catalysts": [
                {"name": name, "count": count} for name, count in self.top_catalysts
            ],
            "latest": self.latest,
        }


@dataclass(slots=True)
class PulseSnapshot:
    metrics: PulseLedgerMetrics
    resonance: Optional[str]
    recent: List[dict[str, str]]

    def to_dict(self) -> dict:
        return {
            "metrics": self.metrics.to_dict(),
            "resonance": self.resonance,
            "recent": list(self.recent),
        }


@dataclass(slots=True)
class ObservatorySnapshot:
    snapshot: ContinuumSnapshot
    lane_highlights: List[LaneStats]

    def to_dict(self) -> dict:
        return {
            "snapshot": self.snapshot.to_dict(),
            "lane_highlights": [stats.to_dict() for stats in self.lane_highlights],
        }


@dataclass(slots=True)
class SnapshotReport:
    generated_at: datetime
    health: ContinuumHealthReport
    wish_summary: str
    wish_snapshot: WishSnapshot
    pulse_snapshot: PulseSnapshot
    observatory: Optional[ObservatorySnapshot]
    warnings: List[str]

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at.isoformat(),
            "health": self.health.to_dict(),
            "wish_summary": self.wish_summary,
            "wish_snapshot": self.wish_snapshot.to_dict(),
            "pulse_snapshot": self.pulse_snapshot.to_dict(),
            "observatory": self.observatory.to_dict() if self.observatory else None,
            "warnings": list(self.warnings),
        }

    def describe(self) -> str:
        lines = [
            "Echo Continuum Snapshot",
            "=" * 24,
            f"Generated: {self.generated_at.isoformat()}",
            "",
            self.health.describe(),
            "",
            "Wish Manifest",
            "-" * 13,
        ]
        lines.extend(self.wish_summary.splitlines())
        lines.append("")

        metrics = self.pulse_snapshot.metrics
        lines.extend(
            [
                "Pulse Ledger",
                "-" * 12,
                f"Status: {metrics.status}",
                f"Total events: {metrics.total_events}",
            ]
        )

        if metrics.last_timestamp_iso:
            last_age = _format_duration(metrics.time_since_last_seconds)
            lines.append(f"Last event: {metrics.last_timestamp_iso} ({last_age} ago)")

        if metrics.cadence_score is not None:
            lines.append(
                f"Cadence: {metrics.cadence_rating} ({metrics.cadence_score:.1f}/100)"
            )
        if metrics.expected_next_timestamp_iso:
            overdue = _format_duration(metrics.overdue_seconds)
            lines.append(
                "Expected next: "
                f"{metrics.expected_next_timestamp_iso} (overdue {overdue})"
            )
        if self.pulse_snapshot.resonance:
            lines.append(f"Resonance: {self.pulse_snapshot.resonance}")

        if self.pulse_snapshot.recent:
            lines.append("")
            lines.append("Recent pulses:")
            for event in self.pulse_snapshot.recent:
                lines.append(f"- {event['timestamp_iso']} :: {event['message']}")

        if self.observatory:
            lines.append("")
            lines.append("Continuum Observatory")
            lines.append("-" * 21)
            snapshot = self.observatory.snapshot
            lines.append(f"Root: {snapshot.root}")
            lines.append(f"Files: {snapshot.total_files:,}")
            lines.append(f"Footprint: {_human_bytes(snapshot.total_bytes)}")
            lines.append(f"Last update: {_format_mtime(snapshot.latest_mtime)}")
            if self.observatory.lane_highlights:
                lines.append("")
                lines.append("Lane highlights:")
                for stats in self.observatory.lane_highlights:
                    freshness = (
                        f"{stats.freshness_days:.1f}d"
                        if stats.freshness_days is not None
                        else "n/a"
                    )
                    lines.append(
                        f"- {stats.lane}: {stats.file_count} files, "
                        f"{stats.doc_count} docs, {stats.code_count} code "
                        f"(freshness {freshness})"
                    )

        if self.warnings:
            lines.append("")
            lines.append("Warnings")
            lines.append("-" * 8)
            for warning in self.warnings:
                lines.append(f"- {warning}")

        return "\n".join(lines)


def build_snapshot(
    *,
    plan_path: Path,
    manifest_path: Path,
    pulses_path: Path,
    warning_hours: float = 24.0,
    critical_hours: float = 72.0,
    recent_limit: int = 5,
    include_observatory: bool = False,
    observatory_root: Optional[Path] = None,
    lane_limit: int = 5,
) -> SnapshotReport:
    warnings: List[str] = []

    health = generate_continuum_health(plan_path, manifest_path, pulses_path)

    manifest = _load_json_file(manifest_path, warnings, label="wish manifest")
    wish_summary = summarize_wishes(manifest or {})
    wish_snapshot = _summarize_wishes_structured(manifest or {})

    pulse_events, resonance = _load_pulses(pulses_path, warnings)
    metrics = compute_pulse_metrics(
        pulse_events,
        warning_hours=warning_hours,
        critical_hours=critical_hours,
    )
    recent = _format_recent_pulses(pulse_events, recent_limit)
    pulse_snapshot = PulseSnapshot(metrics=metrics, resonance=resonance, recent=recent)

    observatory: Optional[ObservatorySnapshot] = None
    if include_observatory:
        root = observatory_root or Path.cwd()
        snapshot = ContinuumObservatory(root).scan()
        lane_highlights = _select_lane_highlights(snapshot, lane_limit)
        observatory = ObservatorySnapshot(snapshot=snapshot, lane_highlights=lane_highlights)

    return SnapshotReport(
        generated_at=datetime.now(timezone.utc),
        health=health,
        wish_summary=wish_summary,
        wish_snapshot=wish_snapshot,
        pulse_snapshot=pulse_snapshot,
        observatory=observatory,
        warnings=warnings,
    )


def _summarize_wishes_structured(manifest: dict) -> WishSnapshot:
    wishes = list(manifest.get("wishes", []) or [])
    total = len(wishes)
    unique_wishers = len({wish.get("wisher", "") for wish in wishes if wish.get("wisher")})
    statuses: dict[str, int] = {}
    catalyst_counts: dict[str, int] = {}
    latest_entry: Optional[dict[str, str]] = None
    latest_time = datetime.fromtimestamp(0, tz=timezone.utc)

    for wish in wishes:
        status = wish.get("status", "unknown") or "unknown"
        statuses[status] = statuses.get(status, 0) + 1
        for catalyst in wish.get("catalysts", []) or []:
            catalyst = str(catalyst).strip()
            if catalyst:
                catalyst_counts[catalyst] = catalyst_counts.get(catalyst, 0) + 1
        created_at = _parse_timestamp(wish.get("created_at"))
        if created_at >= latest_time:
            latest_time = created_at
            latest_entry = {
                "created_at": created_at.isoformat(),
                "wisher": wish.get("wisher", "unknown") or "unknown",
                "desire": wish.get("desire", "?") or "?",
                "status": status,
            }

    top_catalysts = sorted(catalyst_counts.items(), key=lambda item: (-item[1], item[0]))
    return WishSnapshot(
        total=total,
        unique_wishers=unique_wishers,
        statuses=statuses,
        top_catalysts=top_catalysts[:3],
        latest=latest_entry,
    )


def _load_json_file(path: Path, warnings: List[str], *, label: str) -> Optional[dict]:
    if not path.exists():
        warnings.append(f"{label} missing at {path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        warnings.append(f"{label} invalid JSON: {exc}")
        return None
    if isinstance(payload, dict):
        return payload
    warnings.append(f"{label} JSON root is not an object")
    return None


def _load_pulses(path: Path, warnings: List[str]) -> tuple[List[PulseEvent], Optional[str]]:
    if not path.exists():
        warnings.append(f"pulse history missing at {path}")
        return [], None
    try:
        kernel = EchoCodexKernel(pulse_file=str(path))
    except json.JSONDecodeError as exc:
        warnings.append(f"pulse history invalid JSON: {exc}")
        return [], None
    return kernel.history, kernel.resonance() if kernel.history else None


def _format_recent_pulses(events: Sequence[PulseEvent], limit: int) -> List[dict[str, str]]:
    if limit <= 0:
        return []
    recent = events[-limit:]
    return [
        {
            "timestamp_iso": _format_timestamp(event.timestamp),
            "message": event.message,
            "hash": event.hash,
        }
        for event in recent
    ]


def _select_lane_highlights(snapshot: ContinuumSnapshot, limit: int) -> List[LaneStats]:
    lanes = list(snapshot.lanes.values())
    lanes.sort(key=lambda stats: stats.file_count, reverse=True)
    if limit > 0:
        lanes = lanes[:limit]
    return lanes


def _parse_timestamp(value: Optional[str]) -> datetime:
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except ValueError:
        return datetime.fromtimestamp(0, tz=timezone.utc)


def _format_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "n/a"
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        return f"{seconds / 60:.1f}m"
    if seconds < 86400:
        return f"{seconds / 3600:.1f}h"
    return f"{seconds / 86400:.1f}d"


def _format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def _format_mtime(timestamp: float) -> str:
    if timestamp == 0:
        return "n/a"
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def _human_bytes(num_bytes: int) -> str:
    if num_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    index = 0
    value = float(num_bytes)
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    return f"{value:.1f} {units[index]}"


__all__ = [
    "SnapshotReport",
    "WishSnapshot",
    "PulseSnapshot",
    "ObservatorySnapshot",
    "build_snapshot",
]
