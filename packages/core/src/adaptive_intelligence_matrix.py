from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@dataclass
class MatrixConfig:
    """Configuration for orchestrating Adaptive Intelligence scans."""

    repo_root: Path = field(default_factory=_default_repo_root)
    pulse_history_path: Optional[Path] = None
    roadmap_summary_path: Optional[Path] = None
    next_cycle_plan_path: Optional[Path] = None
    pulse_latency_threshold: float = 3 * 3600.0
    cadence_reference_seconds: float = 1800.0
    automation_todo_threshold: int = 12
    adaptability_reference_actions: int = 6

    def __post_init__(self) -> None:
        if self.pulse_history_path is None:
            self.pulse_history_path = self.repo_root / "pulse_history.json"
        if self.roadmap_summary_path is None:
            self.roadmap_summary_path = self.repo_root / "roadmap_summary.json"
        if self.next_cycle_plan_path is None:
            self.next_cycle_plan_path = self.repo_root / "docs" / "NEXT_CYCLE_PLAN.md"


@dataclass
class SignalInsight:
    key: str
    label: str
    status: str
    metrics: Dict[str, object]
    recommendations: List[str] = field(default_factory=list)


class SignalProbe:
    key: str
    label: str

    def collect(self) -> SignalInsight:  # pragma: no cover - interface definition
        raise NotImplementedError


class PulseHistoryProbe(SignalProbe):
    def __init__(self, path: Path, *, latency_threshold: float, cadence_reference: float) -> None:
        self.path = path
        self.key = "pulse_history"
        self.label = "Continuum Pulse"
        self.latency_threshold = latency_threshold
        self.cadence_reference = cadence_reference

    def collect(self) -> SignalInsight:
        if not self.path.exists():
            return SignalInsight(
                key=self.key,
                label=self.label,
                status="missing",
                metrics={},
                recommendations=[f"Create {self.path} to track the continuum pulse"],
            )

        raw = json.loads(self.path.read_text(encoding="utf-8"))
        timestamps = sorted(entry["timestamp"] for entry in raw) if raw else []
        latest_ts = timestamps[-1] if timestamps else None
        cadence = None
        if len(timestamps) > 1:
            diffs = [b - a for a, b in zip(timestamps[:-1], timestamps[1:])]
            cadence = statistics.fmean(diffs)
        now = time.time()
        gap = None if latest_ts is None else max(0.0, now - latest_ts)

        if latest_ts is None:
            status = "no-data"
        elif gap <= self.latency_threshold:
            status = "nominal"
        elif gap <= self.latency_threshold * 2:
            status = "lagging"
        else:
            status = "degraded"

        recs: List[str] = []
        if status != "nominal":
            recs.append(
                "Record a fresh continuum pulse (python -m echo.echoctl cycle) to keep the signal responsive."
            )
        if cadence and cadence > self.cadence_reference * 1.5:
            recs.append("Automate pulse emission or decrease intervals to stabilize cadence.")

        metrics: Dict[str, object] = {
            "events": len(raw),
            "latest_timestamp": latest_ts,
            "seconds_since_last": gap,
            "average_cadence": cadence,
        }
        return SignalInsight(key=self.key, label=self.label, status=status, metrics=metrics, recommendations=recs)


class RoadmapSummaryProbe(SignalProbe):
    def __init__(self, path: Path, *, automation_threshold: int) -> None:
        self.path = path
        self.key = "roadmap_summary"
        self.label = "Roadmap Density"
        self.automation_threshold = automation_threshold

    def collect(self) -> SignalInsight:
        if not self.path.exists():
            return SignalInsight(
                key=self.key,
                label=self.label,
                status="missing",
                metrics={},
                recommendations=[
                    "Run `python -m next_level --roadmap ROADMAP.md` or `python next_level.py` equivalent to generate roadmap_summary.json."
                ],
            )

        summary = json.loads(self.path.read_text(encoding="utf-8"))
        totals = summary.get("totals", {})
        todo_total = int(totals.get("overall", 0))
        per_tag = totals.get("per_tag", {})
        per_location = totals.get("per_location", {})

        status = "nominal" if todo_total <= self.automation_threshold else "pressurized"
        recs: List[str] = []
        if todo_total > self.automation_threshold:
            recs.append(
                f"Detected {todo_total} TODO/FIXME markers – consider triaging automatically with `python -m echo.echoctl plan`."
            )

        metrics: Dict[str, object] = {
            "todo_total": todo_total,
            "per_tag": per_tag,
            "per_location": per_location,
        }
        return SignalInsight(key=self.key, label=self.label, status=status, metrics=metrics, recommendations=recs)


class NextCyclePlanProbe(SignalProbe):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.key = "next_cycle_plan"
        self.label = "Next Cycle Plan"

    def collect(self) -> SignalInsight:
        if not self.path.exists():
            return SignalInsight(
                key=self.key,
                label=self.label,
                status="missing",
                metrics={},
                recommendations=["Generate docs/NEXT_CYCLE_PLAN.md before invoking the adaptive matrix."],
            )

        lines = self.path.read_text(encoding="utf-8").splitlines()
        current_section: Optional[str] = None
        recent_deltas: List[str] = []
        actions: List[str] = []
        success_criteria: List[str] = []
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("## "):
                current_section = line[3:].strip().lower()
                continue
            if current_section == "recent deltas" and line.startswith("*"):
                recent_deltas.append(line.lstrip("* "))
            elif current_section == "proposed actions" and line.startswith("-"):
                actions.append(line.lstrip("- "))
            elif current_section == "success criteria" and line.startswith("-"):
                success_criteria.append(line.lstrip("- "))

        status = "nominal" if actions else "needs-alignment"
        recs: List[str] = []
        if not actions:
            recs.append("Add at least one proposed action so the matrix can evaluate adaptability.")
        if actions and len(success_criteria) < len(actions):
            recs.append("Define success criteria for each proposed action to tighten adaptability loops.")

        metrics: Dict[str, object] = {
            "recent_deltas": recent_deltas,
            "actions": actions,
            "success_criteria": success_criteria,
        }
        return SignalInsight(key=self.key, label=self.label, status=status, metrics=metrics, recommendations=recs)


@dataclass
class AdaptiveIntelReport:
    generated_at: datetime
    summary: str
    composite_scores: Dict[str, float]
    signals: List[SignalInsight]
    context: Dict[str, object]

    def to_text(self) -> str:
        lines = [
            f"Adaptive Intelligence Matrix @ {self.generated_at.isoformat()}",
            f"Summary        : {self.summary}",
            "Composite Scores:",
        ]
        for key, value in self.composite_scores.items():
            lines.append(f"  - {key}: {value:.3f}")
        lines.append("")
        for signal in self.signals:
            lines.append(f"[{signal.status.upper()}] {signal.label}")
            for metric_key, metric_value in signal.metrics.items():
                lines.append(f"    {metric_key}: {metric_value}")
            if signal.recommendations:
                lines.append("    Recommendations:")
                for rec in signal.recommendations:
                    lines.append(f"      * {rec}")
            lines.append("")
        return "\n".join(lines).rstrip()

    def to_dict(self) -> Dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "summary": self.summary,
            "composite_scores": self.composite_scores,
            "signals": [
                {
                    "key": signal.key,
                    "label": signal.label,
                    "status": signal.status,
                    "metrics": signal.metrics,
                    "recommendations": signal.recommendations,
                }
                for signal in self.signals
            ],
            "context": self.context,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        lines = [
            "# Adaptive Intelligence Matrix",
            "",
            f"*Generated at:* {self.generated_at.isoformat()}",
            "",
            "## Composite Scores",
            "| Score | Value |",
            "| --- | --- |",
        ]
        for key, value in self.composite_scores.items():
            lines.append(f"| {key} | {value:.3f} |")

        lines.extend([
            "",
            "## Signals",
            "| Label | Status | Key Metrics | Recommendations |",
            "| --- | --- | --- | --- |",
        ])
        for signal in self.signals:
            metric_summary = ", ".join(f"{k}: {v}" for k, v in signal.metrics.items()) or "-"
            recommendations = "<br />".join(signal.recommendations) if signal.recommendations else "-"
            lines.append(f"| {signal.label} | {signal.status} | {metric_summary} | {recommendations} |")

        return "\n".join(lines)


class AdaptiveIntelligenceMatrix:
    """High-order subsystem that fuses operational signals into adaptive guidance."""

    def __init__(self, config: MatrixConfig, probes: Optional[Iterable[SignalProbe]] = None) -> None:
        self.config = config
        if probes is None:
            probes = [
                PulseHistoryProbe(
                    self.config.pulse_history_path,
                    latency_threshold=self.config.pulse_latency_threshold,
                    cadence_reference=self.config.cadence_reference_seconds,
                ),
                RoadmapSummaryProbe(
                    self.config.roadmap_summary_path,
                    automation_threshold=self.config.automation_todo_threshold,
                ),
                NextCyclePlanProbe(self.config.next_cycle_plan_path),
            ]
        self.probes = list(probes)

    def generate_report(self) -> AdaptiveIntelReport:
        signals = [probe.collect() for probe in self.probes]
        composite_scores = self._derive_composite_scores(signals)
        summary = self._summarize(composite_scores)
        context = {
            "pulse_history_path": str(self.config.pulse_history_path),
            "roadmap_summary_path": str(self.config.roadmap_summary_path),
            "next_cycle_plan_path": str(self.config.next_cycle_plan_path),
        }
        return AdaptiveIntelReport(
            generated_at=datetime.now(tz=timezone.utc),
            summary=summary,
            composite_scores=composite_scores,
            signals=signals,
            context=context,
        )

    def _derive_composite_scores(self, signals: List[SignalInsight]) -> Dict[str, float]:
        score_map: Dict[str, float] = {}
        status_weights = {"nominal": 1.0, "pressurized": 0.5, "lagging": 0.6, "degraded": 0.2, "missing": 0.0, "no-data": 0.3}
        status_weights.update({"needs-alignment": 0.4})

        automation_pressure = 0.0
        adaptability_index = 0.0
        health_scores: List[float] = []

        for signal in signals:
            metrics = signal.metrics
            if signal.key == "roadmap_summary" and metrics:
                todo_total = int(metrics.get("todo_total", 0))
                automation_pressure = min(1.0, todo_total / max(1, self.config.automation_todo_threshold))
            elif signal.key == "pulse_history" and metrics:
                seconds_since_last = metrics.get("seconds_since_last") or 0.0
                latency_ratio = min(1.0, float(seconds_since_last) / max(1.0, self.config.pulse_latency_threshold))
                automation_pressure = min(1.0, automation_pressure * 0.5 + latency_ratio * 0.5)
            elif signal.key == "next_cycle_plan" and metrics:
                actions = metrics.get("actions", [])
                success = metrics.get("success_criteria", [])
                if actions:
                    coverage = len(success) / len(actions)
                    action_ratio = min(1.0, len(actions) / max(1, self.config.adaptability_reference_actions))
                    adaptability_index = min(1.0, 0.2 + 0.4 * action_ratio + 0.4 * coverage)
                else:
                    adaptability_index = 0.1

            health_scores.append(status_weights.get(signal.status, 0.5))

        if not signals:
            signal_health = 0.0
        else:
            signal_health = sum(health_scores) / len(health_scores)

        score_map["automation_pressure"] = round(automation_pressure, 3)
        score_map["adaptability_index"] = round(adaptability_index, 3)
        score_map["signal_health"] = round(signal_health, 3)
        execution_ready = (adaptability_index * 0.45) + ((1 - automation_pressure) * 0.35) + (signal_health * 0.2)
        score_map["execution_ready"] = round(max(0.0, min(1.0, execution_ready)), 3)
        return score_map

    @staticmethod
    def _summarize(scores: Dict[str, float]) -> str:
        return (
            "Signal health {signal_health:.2f}, automation pressure {automation_pressure:.2f}, "
            "adaptability index {adaptability_index:.2f}, execution ready {execution_ready:.2f}."
        ).format(**scores)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adaptive Intelligence Matrix orchestrator")
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional repository root override")
    parser.add_argument("--emit-json", type=Path, default=None, help="Write the matrix report to a JSON file")
    parser.add_argument("--emit-markdown", type=Path, default=None, help="Write the matrix report to a Markdown file")
    parser.add_argument("--quiet", action="store_true", help="Skip printing the human-readable report")
    return parser


def main(argv: Optional[List[str]] = None) -> AdaptiveIntelReport:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    repo_root = args.repo_root or _default_repo_root()
    config = MatrixConfig(repo_root=repo_root)
    matrix = AdaptiveIntelligenceMatrix(config)
    report = matrix.generate_report()

    if not args.quiet:
        print(report.to_text())
    if args.emit_json:
        args.emit_json.write_text(report.to_json(), encoding="utf-8")
    if args.emit_markdown:
        args.emit_markdown.write_text(report.to_markdown(), encoding="utf-8")
    return report


if __name__ == "__main__":
    main()
