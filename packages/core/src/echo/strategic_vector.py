"""Strategic vector synthesis for the Echo ecosystem.

This module introduces the :class:`StrategicVectorReport`, a composite signal that
distils several of Echo's core telemetry feeds into a single actionable view.
It analyses the repository manifest, cycle timeline, capability registry, and
ecosystem pulse to surface momentum, coverage, and operational readiness
insights.  The goal is to provide a *decision-grade* snapshot that can be fed
to external dashboards, operators, or autonomous agents without recomputing the
underlying analytics in multiple locations.

The report is intentionally deterministic: each signal produces a bounded score
between ``0`` and ``1`` along with structured metadata that explains the
result.  Downstream systems can serialise the report to JSON or render a rich
Markdown briefing.  Helper functions are provided to export the report to disk
and to gather live data from the repository, but the core synthesis pipeline is
pure and easy to unit test by supplying precomputed payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import fmean
from typing import Iterable, Mapping, MutableMapping, Sequence

from ._paths import MANIFEST_ROOT, REPO_ROOT
from .ecosystem_pulse import EcosystemPulse, EcosystemPulseReport
from .echo_capability_engine import CAPABILITIES, list_capabilities
from .manifest_cli import MANIFEST_NAME


__all__ = [
    "StrategicSignal",
    "StrategicVectorReport",
    "build_strategic_vector",
    "generate_strategic_vector",
    "export_strategic_vector",
]


_DEFAULT_MANIFEST_PATHS: tuple[Path, ...] = (
    REPO_ROOT / MANIFEST_NAME,
    MANIFEST_ROOT / MANIFEST_NAME,
)

_DEFAULT_TIMELINE_PATHS: tuple[Path, ...] = (
    REPO_ROOT / "artifacts" / "cycle_timeline.json",
    MANIFEST_ROOT / "release-1.0.0.json",
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _load_json(path: Path) -> Mapping[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _load_manifest_entries(paths: Iterable[Path]) -> list[Mapping[str, object]]:
    for path in paths:
        data = _load_json(path)
        if data:
            entries = data.get("entries")
            if isinstance(entries, list):
                return [entry for entry in entries if isinstance(entry, Mapping)]
    return []


def _load_timeline_cycles(paths: Iterable[Path]) -> list[Mapping[str, object]]:
    for path in paths:
        data = _load_json(path)
        if not data:
            continue
        cycles = data.get("cycles")
        if isinstance(cycles, list):
            return [cycle for cycle in cycles if isinstance(cycle, Mapping)]
    return []


@dataclass(frozen=True)
class StrategicSignal:
    """Single strategic dimension contributing to the composite vector."""

    name: str
    title: str
    score: float
    weight: float
    summary: str
    details: Mapping[str, object]
    insights: tuple[str, ...] = ()

    def to_dict(self) -> Mapping[str, object]:
        return {
            "name": self.name,
            "title": self.title,
            "score": round(self.score, 4),
            "weight": round(self.weight, 4),
            "summary": self.summary,
            "details": dict(self.details),
            "insights": list(self.insights),
        }


@dataclass(frozen=True)
class StrategicVectorReport:
    """Composite view of Echo's strategic operating posture."""

    generated_at: datetime
    signals: tuple[StrategicSignal, ...]
    metadata: Mapping[str, object]

    @property
    def overall_score(self) -> float:
        if not self.signals:
            return 0.0
        total_weight = sum(signal.weight for signal in self.signals)
        if total_weight <= 0:
            return 0.0
        weighted = sum(signal.score * signal.weight for signal in self.signals)
        return round(weighted / total_weight, 4)

    def to_dict(self) -> Mapping[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "overall_score": round(self.overall_score, 4),
            "signals": [signal.to_dict() for signal in self.signals],
            "metadata": dict(self.metadata),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def render_markdown(self) -> str:
        lines = ["# Echo Strategic Vector", ""]
        lines.append(f"Generated: {self.generated_at.isoformat()}")
        lines.append(f"Composite score: {self.overall_score:.3f}")
        lines.append("")
        lines.append("| Signal | Score | Weight | Summary |")
        lines.append("| --- | ---: | ---: | --- |")
        for signal in self.signals:
            lines.append(
                f"| {signal.title} | {signal.score:.3f} | {signal.weight:.2f} | {signal.summary} |"
            )
        lines.append("")
        lines.append("## Insights")
        for signal in self.signals:
            lines.append(f"### {signal.title}")
            if signal.insights:
                for insight in signal.insights:
                    lines.append(f"- {insight}")
            else:
                lines.append("- No blocking issues detected.")
            lines.append("")
        if self.metadata:
            lines.append("## Metadata")
            for key, value in sorted(self.metadata.items()):
                lines.append(f"- **{key}**: {value}")
            lines.append("")
        return "\n".join(lines).strip() + "\n"


def _manifest_signal(entries: Sequence[Mapping[str, object]]) -> StrategicSignal:
    total_entries = len(entries)
    categories = {str(entry.get("category", "")) for entry in entries if entry.get("category")}
    tags: set[str] = set()
    owners = 0
    fresh_entries = 0
    now = _utcnow()
    for entry in entries:
        entry_tags = entry.get("tags")
        if isinstance(entry_tags, Iterable):
            tags.update(str(tag) for tag in entry_tags)
        entry_owners = entry.get("owners")
        if isinstance(entry_owners, Iterable) and any(str(owner).strip() for owner in entry_owners):
            owners += 1
        last_modified = entry.get("last_modified")
        if isinstance(last_modified, str) and last_modified:
            try:
                timestamp = datetime.fromisoformat(last_modified)
            except ValueError:
                continue
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            age = (now - timestamp).total_seconds() / 86400
            if age <= 90:
                fresh_entries += 1

    if total_entries == 0:
        summary = "No manifest entries available."
        details = {"entries": 0}
        insights = ("Run `echo manifest refresh` to seed the strategic vector.",)
        return StrategicSignal(
            name="manifest",
            title="Manifest Coverage",
            score=0.0,
            weight=0.30,
            summary=summary,
            details=details,
            insights=insights,
        )

    diversity_target = max(4, int(total_entries ** 0.5) + 2)
    category_score = _clamp(len(categories) / diversity_target)
    owner_score = _clamp(owners / total_entries)
    freshness_score = _clamp(fresh_entries / max(1, min(total_entries, 24)))
    tag_score = _clamp(len(tags) / max(1, len(categories) * 3)) if categories else 0.0

    score = 0.4 * category_score + 0.25 * owner_score + 0.2 * freshness_score + 0.15 * tag_score
    summary = (
        f"{len(categories)} focus areas with {total_entries} assets; "
        f"{owner_score*100:.0f}% owner coverage."
    )
    insights: list[str] = []
    if category_score < 0.45:
        insights.append("Expand coverage across additional manifest categories.")
    if owner_score < 0.6:
        insights.append("Increase CODEOWNERS mapping to lift accountability.")
    if freshness_score < 0.5:
        insights.append("Refresh key artifacts to reduce staleness.")
    if tag_score < 0.35:
        insights.append("Diversify manifest tagging to strengthen discovery.")

    details = {
        "entries": total_entries,
        "categories": len(categories),
        "tags": len(tags),
        "entries_with_owners": owners,
        "recent_entries_90d": fresh_entries,
    }
    return StrategicSignal(
        name="manifest",
        title="Manifest Coverage",
        score=round(score, 4),
        weight=0.30,
        summary=summary,
        details=details,
        insights=tuple(insights),
    )


def _timeline_signal(cycles: Sequence[Mapping[str, object]]) -> StrategicSignal:
    if not cycles:
        return StrategicSignal(
            name="timeline",
            title="Cycle Momentum",
            score=0.0,
            weight=0.25,
            summary="No cycle timeline data discovered.",
            details={"cycles": 0},
            insights=("Generate cycle timeline artifacts to activate momentum tracking.",),
        )

    now = _utcnow()
    pulse_counts: list[int] = []
    puzzle_counts: list[int] = []
    harmonic_counts: list[int] = []
    recency_days: list[float] = []
    for cycle in cycles:
        pulses = cycle.get("pulses")
        pulse_counts.append(len(pulses) if isinstance(pulses, list) else 0)
        puzzles = cycle.get("puzzles")
        puzzle_counts.append(len(puzzles) if isinstance(puzzles, list) else 0)
        harmonics = cycle.get("harmonics")
        harmonic_counts.append(len(harmonics) if isinstance(harmonics, list) else 0)
        snapshot = cycle.get("snapshot")
        if isinstance(snapshot, Mapping):
            timestamp = snapshot.get("timestamp")
            if isinstance(timestamp, str):
                try:
                    moment = datetime.fromisoformat(timestamp)
                except ValueError:
                    continue
                if moment.tzinfo is None:
                    moment = moment.replace(tzinfo=timezone.utc)
                recency_days.append(max(0.0, (now - moment).total_seconds() / 86400))

    average_pulses = fmean(pulse_counts) if pulse_counts else 0.0
    average_puzzles = fmean(puzzle_counts) if puzzle_counts else 0.0
    average_harmonics = fmean(harmonic_counts) if harmonic_counts else 0.0
    min_recency = min(recency_days) if recency_days else 180.0

    pulse_score = _clamp(average_pulses / 5.0)
    puzzle_score = _clamp(average_puzzles / 1.5)
    harmonic_score = _clamp(average_harmonics / 3.0)
    recency_score = _clamp(1.0 - (min_recency / 60.0))

    score = 0.4 * recency_score + 0.3 * pulse_score + 0.2 * puzzle_score + 0.1 * harmonic_score
    summary = (
        f"Avg {average_pulses:.1f} pulses & {average_puzzles:.1f} puzzles per cycle; "
        f"latest cycle {min_recency:.0f} days old."
    )
    insights: list[str] = []
    if recency_score < 0.5:
        insights.append("Run a fresh cycle to keep the cadence within a 60-day window.")
    if pulse_score < 0.5:
        insights.append("Increase pulse activity to capture narrative flow.")
    if puzzle_score < 0.4:
        insights.append("Activate puzzle threads to expand engagement signals.")
    if harmonic_score < 0.4:
        insights.append("Feed bridge harmonics to enrich cross-cycle resonance.")

    details = {
        "cycles": len(cycles),
        "avg_pulses": round(average_pulses, 2),
        "avg_puzzles": round(average_puzzles, 2),
        "avg_harmonics": round(average_harmonics, 2),
        "freshest_cycle_age_days": round(min_recency, 2),
    }
    return StrategicSignal(
        name="timeline",
        title="Cycle Momentum",
        score=round(score, 4),
        weight=0.25,
        summary=summary,
        details=details,
        insights=tuple(insights),
    )


def _capability_signal(registry: Mapping[str, Mapping[str, object]]) -> StrategicSignal:
    names = [name for name in registry.keys()]
    count = len(names)
    if count == 0:
        return StrategicSignal(
            name="capabilities",
            title="Capability Arsenal",
            score=0.0,
            weight=0.20,
            summary="Capability registry is empty.",
            details={"capabilities": 0},
            insights=("Register high-leverage capabilities via `echo.echo_capability_engine`.",),
        )

    descriptions = [str(registry[name].get("description", "")) for name in names]
    unique_keywords: set[str] = set()
    for description in descriptions:
        for token in description.replace("/", " ").split():
            if len(token) > 4:
                unique_keywords.add(token.lower())

    score = _clamp(count / 12.0) * 0.7 + _clamp(len(unique_keywords) / 30.0) * 0.3
    insights: list[str] = []
    if count < 6:
        insights.append("Expand the capability registry to cover more operational modes.")
    if len(unique_keywords) < max(8, count * 2):
        insights.append("Enrich capability descriptions for discoverability.")

    details = {
        "capabilities": count,
        "unique_keywords": len(unique_keywords),
        "registry_keys": sorted(names),
    }
    summary = f"{count} capabilities registered spanning {len(unique_keywords)} unique themes."
    return StrategicSignal(
        name="capabilities",
        title="Capability Arsenal",
        score=round(_clamp(score), 4),
        weight=0.20,
        summary=summary,
        details=details,
        insights=tuple(insights),
    )


def _ecosystem_signal(report: EcosystemPulseReport | None) -> StrategicSignal:
    if report is None:
        return StrategicSignal(
            name="ecosystem",
            title="Ecosystem Health",
            score=0.0,
            weight=0.25,
            summary="No ecosystem pulse available.",
            details={},
            insights=("Run `EcosystemPulse().generate_report()` to baseline the environment.",),
        )

    score = _clamp(report.overall_score / 100.0)
    low_signals = [signal for signal in report.signals if signal.score < 60.0]
    insights = [
        f"{signal.title} at {signal.score:.1f}; {', '.join(signal.insights) if signal.insights else 'schedule reinforcement.'}"
        for signal in low_signals
    ]
    details = {
        "overall_score": report.overall_score,
        "areas": [signal.to_dict() for signal in report.signals],
    }
    summary = f"Ecosystem health at {report.overall_score:.1f}; {len(low_signals)} areas flagged."
    return StrategicSignal(
        name="ecosystem",
        title="Ecosystem Health",
        score=round(score, 4),
        weight=0.25,
        summary=summary,
        details=details,
        insights=tuple(insights),
    )


def build_strategic_vector(
    *,
    manifest_entries: Sequence[Mapping[str, object]] | None = None,
    timeline_cycles: Sequence[Mapping[str, object]] | None = None,
    ecosystem_report: EcosystemPulseReport | None = None,
    capability_registry: Mapping[str, Mapping[str, object]] | None = None,
    generated_at: datetime | None = None,
) -> StrategicVectorReport:
    """Construct a :class:`StrategicVectorReport` from supplied inputs."""

    manifest_entries = list(manifest_entries or [])
    timeline_cycles = list(timeline_cycles or [])
    capability_registry = dict(capability_registry or {})
    signals = (
        _manifest_signal(manifest_entries),
        _timeline_signal(timeline_cycles),
        _capability_signal(capability_registry),
        _ecosystem_signal(ecosystem_report),
    )

    metadata = {
        "manifest_entries": len(manifest_entries),
        "timeline_cycles": len(timeline_cycles),
        "capability_count": len(capability_registry),
        "ecosystem_surface": len(ecosystem_report.signals)
        if ecosystem_report is not None
        else 0,
    }
    return StrategicVectorReport(
        generated_at=generated_at or _utcnow(),
        signals=tuple(signals),
        metadata=metadata,
    )


def generate_strategic_vector(
    *,
    manifest_paths: Iterable[Path] | None = None,
    timeline_paths: Iterable[Path] | None = None,
    pulse: EcosystemPulse | None = None,
) -> StrategicVectorReport:
    """Gather live repository data and produce a strategic vector report."""

    manifest_entries = _load_manifest_entries(manifest_paths or _DEFAULT_MANIFEST_PATHS)
    timeline_cycles = _load_timeline_cycles(timeline_paths or _DEFAULT_TIMELINE_PATHS)

    ecosystem_report = (pulse or EcosystemPulse()).generate_report()
    capability_registry: MutableMapping[str, Mapping[str, object]] = {}
    for name in list_capabilities():
        metadata = CAPABILITIES.get(name)
        if isinstance(metadata, Mapping):
            capability_registry[name] = dict(metadata)

    return build_strategic_vector(
        manifest_entries=manifest_entries,
        timeline_cycles=timeline_cycles,
        ecosystem_report=ecosystem_report,
        capability_registry=capability_registry,
    )


def export_strategic_vector(
    report: StrategicVectorReport,
    path: Path,
    *,
    format: str = "json",
) -> Path:
    """Serialise *report* to ``path`` using the specified *format*."""

    format_lower = format.lower()
    if format_lower == "json":
        path.write_text(report.to_json(indent=2), encoding="utf-8")
    elif format_lower in {"md", "markdown"}:
        path.write_text(report.render_markdown(), encoding="utf-8")
    else:
        raise ValueError("format must be 'json' or 'markdown'")
    return path


def _main() -> None:  # pragma: no cover - exercised via CLI integration
    import argparse

    parser = argparse.ArgumentParser(description="Generate the Echo strategic vector report.")
    parser.add_argument("--json", dest="json_path", type=Path, help="Optional JSON export path.")
    parser.add_argument(
        "--markdown", dest="markdown_path", type=Path, help="Optional Markdown export path."
    )
    args = parser.parse_args()

    report = generate_strategic_vector()
    if args.json_path:
        export_strategic_vector(report, args.json_path, format="json")
    if args.markdown_path:
        export_strategic_vector(report, args.markdown_path, format="markdown")
    if not args.json_path and not args.markdown_path:
        print(report.render_markdown())


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    _main()

