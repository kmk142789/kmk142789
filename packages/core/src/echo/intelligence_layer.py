"""Synthesis utilities for harmonising Echo's intelligence capabilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

from .coordination_mesh import ManifestNotFoundError, build_coordination_mesh
from .ecosystem_pulse import (
    EcosystemAreaConfig,
    EcosystemPulse,
    EcosystemPulseReport,
    EcosystemSignal,
)
from .evolver import (
    _MOMENTUM_SENSITIVITY,
    _classify_momentum,
    _confidence_from_momentum,
    _describe_momentum,
    _momentum_glyph,
)

__all__ = [
    "IntelligenceLayerSnapshot",
    "synthesize_intelligence_layer",
]


def _coerce_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    if isinstance(value, Path):
        return value
    return Path(str(value))


def _coerce_area_config(raw: EcosystemAreaConfig | Mapping[str, object]) -> EcosystemAreaConfig:
    if isinstance(raw, EcosystemAreaConfig):
        return raw

    if not isinstance(raw, Mapping):
        raise TypeError("ecosystem area configuration must be a mapping or EcosystemAreaConfig instance")

    data: MutableMapping[str, object] = dict(raw)
    required = data.get("required")
    if required is None:
        required_paths: Sequence[Path] = ()
    else:
        required_paths = tuple(Path(str(item)) for item in required)  # type: ignore[arg-type]

    return EcosystemAreaConfig(
        key=str(data.get("key")),
        title=str(data.get("title")),
        relative_path=Path(str(data.get("relative_path"))),
        description=str(data.get("description", "")),
        required=required_paths,
        freshness_days=int(data.get("freshness_days", EcosystemPulse.DEFAULT_AREAS[0].freshness_days)),
        volume_hint=int(data.get("volume_hint", EcosystemPulse.DEFAULT_AREAS[0].volume_hint)),
    )


def _coerce_momentum_samples(samples: Sequence[float | int | str | object] | None) -> List[float]:
    if not samples:
        return []
    coerced: List[float] = []
    for sample in samples:
        try:
            coerced.append(float(sample))
        except (TypeError, ValueError):
            raise TypeError("momentum_samples must contain numeric values") from None
    return coerced


def _coerce_threshold(threshold: float | int | str | None) -> float | None:
    if threshold is None:
        return None
    try:
        value = float(threshold)
    except (TypeError, ValueError):  # pragma: no cover - defensive path
        raise TypeError("momentum_threshold must be numeric") from None
    if value <= 0:
        raise ValueError("momentum_threshold must be positive")
    return value


def _momentum_snapshot(
    *,
    samples: Sequence[float],
    threshold: float | None,
) -> Dict[str, object]:
    effective_threshold = float(threshold) if threshold is not None else _MOMENTUM_SENSITIVITY

    if not samples:
        return {
            "cycle": None,
            "values": [],
            "percent_values": [],
            "sample_count": 0,
            "threshold": effective_threshold,
            "status": "unavailable",
            "trend": "no signal",
            "confidence": "low",
            "glyph_arc": "",
            "summary": "Momentum history unavailable; provide samples to activate the resonance layer.",
        }

    values = list(samples)
    average = sum(values) / len(values)
    minimum = min(values)
    maximum = max(values)
    span = maximum - minimum
    latest = values[-1]

    status = _classify_momentum(latest, threshold=effective_threshold)
    trend = _describe_momentum(latest, average=average, threshold=effective_threshold)
    confidence = _confidence_from_momentum(latest, average=average, threshold=effective_threshold)
    glyph_arc = "".join(_momentum_glyph(sample, threshold=effective_threshold) for sample in values)

    def _direction(sample: float) -> int:
        if sample > effective_threshold:
            return 1
        if sample < -effective_threshold:
            return -1
        return 0

    directions = [_direction(sample) for sample in values]
    current_direction = directions[-1]
    if current_direction > 0:
        direction_label = "positive"
    elif current_direction < 0:
        direction_label = "negative"
    else:
        direction_label = "steady"

    streak = 1
    for previous in reversed(directions[:-1]):
        if previous == current_direction:
            streak += 1
        else:
            break

    direction_changes = sum(
        1 for previous, current in zip(directions, directions[1:]) if current != previous
    )

    summary = (
        "Momentum arc {arc} traces {trend} ({status}, {latest:+.3f}); "
        "average {average:+.3f}, span {span:+.3f}; {label} streak {streak}."
    ).format(
        arc=glyph_arc or "→",
        trend=trend,
        status=status,
        latest=latest,
        average=average,
        span=span,
        label=f"{direction_label} pulse",
        streak=streak,
    )

    return {
        "cycle": None,
        "values": values,
        "percent_values": [sample * 100.0 for sample in values],
        "sample_count": len(values),
        "threshold": effective_threshold,
        "status": status,
        "trend": trend,
        "confidence": confidence,
        "glyph_arc": glyph_arc,
        "latest": latest,
        "latest_percent": latest * 100.0,
        "average": average,
        "average_percent": average * 100.0,
        "minimum": minimum,
        "minimum_percent": minimum * 100.0,
        "maximum": maximum,
        "maximum_percent": maximum * 100.0,
        "span": span,
        "span_percent": span * 100.0,
        "direction": direction_label,
        "direction_changes": direction_changes,
        "streak": streak,
        "summary": summary,
    }


def _momentum_score(status: str, confidence: str) -> float:
    status_weights = {
        "accelerating": 0.85,
        "steady": 0.6,
        "regressing": 0.25,
        "unavailable": 0.0,
    }
    confidence_bonus = {"high": 0.12, "medium": 0.06, "low": 0.0}

    base = status_weights.get(status, 0.4)
    bonus = confidence_bonus.get(confidence, 0.0)
    return max(0.0, min(1.0, base + bonus))


def _coherence_summary(
    *,
    mesh_summary: Mapping[str, object],
    momentum: Mapping[str, object],
    ecosystem_score: float,
) -> Dict[str, object]:
    autonomy_index = float(mesh_summary.get("autonomy_index", 0.0))
    momentum_status = str(momentum.get("status", "unavailable"))
    momentum_confidence = str(momentum.get("confidence", "low"))
    momentum_metric = _momentum_score(momentum_status, momentum_confidence)
    normalized_ecosystem = max(0.0, min(1.0, ecosystem_score / 100.0))

    coherence_score = round(
        (autonomy_index + normalized_ecosystem + momentum_metric) / 3 * 100,
        2,
    )

    if coherence_score >= 80:
        status = "ascending"
    elif coherence_score >= 55:
        status = "steady"
    else:
        status = "fragmented"

    insights: List[str] = []

    if momentum_status == "accelerating":
        insights.append("Momentum surge detected; align constellation clusters to capture the upswing.")
    elif momentum_status == "regressing":
        insights.append("Momentum regression spotted; re-anchor autonomy loops to stabilise progress.")
    else:
        insights.append("Momentum line is steady; maintain current execution cadence.")

    if autonomy_index >= 0.7:
        insights.append("Coordination mesh exhibits high autonomy density across modules.")
    elif autonomy_index <= 0.4:
        insights.append("Autonomy index is thin; nurture multi-owner clusters to widen coverage.")

    if ecosystem_score >= 70:
        insights.append("Ecosystem pulse is healthy with vibrant surface areas.")
    elif ecosystem_score <= 40:
        insights.append("Ecosystem pulse underperforming; reinforce documentation and operational lanes.")

    if not insights:
        insights.append("Systems in equilibrium; continue harmonised iteration cadence.")

    return {
        "coherence_score": coherence_score,
        "status": status,
        "insights": insights,
        "metrics": {
            "autonomy_index": autonomy_index,
            "momentum_signal": momentum_metric,
            "ecosystem_health": normalized_ecosystem,
        },
    }


def _ranked_signals(signals: Sequence[EcosystemSignal] | Sequence[object]) -> List[EcosystemSignal]:
    try:
        typed_signals = list(signals)
    except TypeError:
        return []
    return sorted(typed_signals, key=lambda signal: getattr(signal, "score", 0.0))


def _planning_directives(
    *,
    pulse_report: EcosystemPulseReport,
    momentum: Mapping[str, object],
) -> Dict[str, object]:
    focus_windows: List[Dict[str, object]] = []
    for signal in _ranked_signals(pulse_report.signals)[:3]:
        score = float(getattr(signal, "score", 0.0))
        if score < 40:
            priority = "stabilize"
        elif score < 70:
            priority = "sustain"
        else:
            priority = "amplify"
        focus_windows.append(
            {
                "key": getattr(signal, "key", "unknown"),
                "title": getattr(signal, "title", ""),
                "score": round(score, 2),
                "priority": priority,
                "insights": list(getattr(signal, "insights", []) or []),
            }
        )

    status = str(momentum.get("status", "steady"))
    horizon = {
        "accelerating": "expansion",
        "regressing": "stabilisation",
    }.get(status, "sustainment")

    recommendations: List[str] = []
    if status == "accelerating":
        recommendations.append("Lock in the acceleration by channeling more builders into the strongest clusters.")
    elif status == "regressing":
        recommendations.append("Stabilise cadence with smaller sprints before attempting large jumps.")
    else:
        recommendations.append("Maintain a steady planning horizon while targeting underperforming surfaces.")
    if focus_windows:
        recommendations.append(f"Prioritise {focus_windows[0]['title']} to unblock the downstream modules.")

    return {
        "tempo": status,
        "horizon": horizon,
        "focus": focus_windows,
        "recommendations": recommendations,
    }


def _diagnostic_matrix(
    *,
    mesh_summary: Mapping[str, object],
    pulse_report: EcosystemPulseReport,
) -> Dict[str, object]:
    missing_assets = sum(len(getattr(signal, "missing", [])) for signal in pulse_report.signals)
    dormant = [
        getattr(signal, "title", "")
        for signal in pulse_report.signals
        if getattr(signal, "last_updated", None) is None
    ]
    coverage = float(mesh_summary.get("autonomy_index", 0.0))
    modules = int(mesh_summary.get("modules", 0))
    owners = len(mesh_summary.get("owners", []))

    alerts: List[str] = []
    if missing_assets:
        alerts.append(f"{missing_assets} required artifacts are missing across the ecosystem.")
    if dormant:
        alerts.append("Dormant areas detected: " + ", ".join(dormant[:3]) + ("…" if len(dormant) > 3 else ""))
    if coverage < 0.4:
        alerts.append("Autonomy index is thin; rotate more owners into under-covered modules.")

    return {
        "missing_assets": missing_assets,
        "dormant_areas": dormant,
        "mesh_health": {
            "modules": modules,
            "owners": owners,
            "autonomy_index": round(coverage, 4),
        },
        "alerts": alerts or ["All diagnostics nominal."],
    }


def _adaptation_directives(
    *,
    momentum: Mapping[str, object],
    coherence: Mapping[str, object],
    pulse_report: EcosystemPulseReport,
) -> Dict[str, object]:
    agility = round(float(coherence.get("coherence_score", 0.0)) / 100.0, 3)
    tactics: List[str] = []
    status = str(momentum.get("status", "steady"))
    if status == "accelerating":
        tactics.append("Lean into adaptive loops; reinforce bridges between top scoring ecosystem areas.")
    elif status == "regressing":
        tactics.append("Adopt shorter retrospectives and route decisions through the most active owners.")
    else:
        tactics.append("Maintain current adaptation rhythm with weekly instrumentation sweeps.")

    weakest_signal = next(iter(_ranked_signals(pulse_report.signals)), None)
    if weakest_signal is not None:
        tactics.append(
            f"Route adaptation backlog toward {getattr(weakest_signal, 'title', 'the weakest area')} to close structural gaps."
        )

    return {
        "agility_index": agility,
        "momentum_status": status,
        "tactics": tactics,
    }


def _orchestration_outlook(
    *,
    mesh_dict: Mapping[str, object],
    momentum: Mapping[str, object],
) -> Dict[str, object]:
    clusters = list(mesh_dict.get("clusters", []))
    ranked_modules = sorted(
        clusters,
        key=lambda cluster: len(cluster.get("entries", [])),
        reverse=True,
    )
    top_modules = [
        {
            "module": cluster.get("module"),
            "entry_count": len(cluster.get("entries", [])),
            "categories": cluster.get("categories", {}),
            "owners": list(cluster.get("owners", {}).keys()),
        }
        for cluster in ranked_modules[:3]
    ]

    adjacency = mesh_dict.get("links", [])
    strongest_link = None
    if adjacency:
        strongest_link = max(adjacency, key=lambda link: link.get("weight", 0))

    return {
        "momentum": momentum.get("status", "steady"),
        "top_modules": top_modules,
        "strongest_link": strongest_link,
        "link_count": len(adjacency),
    }


def _high_level_layer(
    *,
    mesh_dict: Mapping[str, object],
    pulse_report: EcosystemPulseReport,
    momentum: Mapping[str, object],
    coherence: Mapping[str, object],
) -> Dict[str, object]:
    return {
        "planning": _planning_directives(pulse_report=pulse_report, momentum=momentum),
        "diagnostics": _diagnostic_matrix(mesh_summary=mesh_dict.get("summary", {}), pulse_report=pulse_report),
        "adaptation": _adaptation_directives(momentum=momentum, coherence=coherence, pulse_report=pulse_report),
        "orchestration": _orchestration_outlook(mesh_dict=mesh_dict, momentum=momentum),
    }


@dataclass(slots=True)
class IntelligenceLayerSnapshot:
    """Composite structure that unifies mesh, momentum, and ecosystem signals."""

    generated_at: str
    mesh: Dict[str, object]
    momentum: Dict[str, object]
    ecosystem: Dict[str, object]
    coherence: Dict[str, object]
    high_level: Dict[str, object]
    context: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "mesh": self.mesh,
            "momentum": self.momentum,
            "ecosystem": self.ecosystem,
            "coherence": self.coherence,
            "high_level": self.high_level,
            "context": self.context,
        }


def synthesize_intelligence_layer(
    *,
    manifest_path: str | Path | None = None,
    repo_root: str | Path | None = None,
    momentum_samples: Sequence[float | int | str | object] | None = None,
    momentum_threshold: float | int | str | None = None,
    ecosystem_areas: Iterable[EcosystemAreaConfig | Mapping[str, object]] | None = None,
) -> IntelligenceLayerSnapshot:
    """Build the higher-order intelligence snapshot linking Echo's capabilities."""

    manifest = _coerce_path(manifest_path)
    repo = _coerce_path(repo_root) or Path.cwd()
    threshold = _coerce_threshold(momentum_threshold)
    samples = _coerce_momentum_samples(momentum_samples)

    if manifest is None:
        try:
            mesh = build_coordination_mesh()
        except ManifestNotFoundError as exc:  # pragma: no cover - runtime safeguard
            raise FileNotFoundError("Unable to locate echo_manifest.json for intelligence synthesis") from exc
    else:
        mesh = build_coordination_mesh(manifest)

    if ecosystem_areas is None:
        areas = None
    else:
        areas = tuple(_coerce_area_config(area) for area in ecosystem_areas)

    pulse = EcosystemPulse(repo_root=repo, areas=areas)
    pulse_report = pulse.generate_report()
    momentum_payload = _momentum_snapshot(samples=samples, threshold=threshold)

    mesh_payload = mesh.as_dict()
    coherence = _coherence_summary(
        mesh_summary=mesh_payload["summary"],
        momentum=momentum_payload,
        ecosystem_score=pulse_report.overall_score,
    )

    high_level = _high_level_layer(
        mesh_dict=mesh_payload,
        pulse_report=pulse_report,
        momentum=momentum_payload,
        coherence=coherence,
    )

    generated_at = datetime.now(timezone.utc).isoformat()

    snapshot = IntelligenceLayerSnapshot(
        generated_at=generated_at,
        mesh=mesh_payload,
        momentum=momentum_payload,
        ecosystem=pulse_report.to_dict(),
        coherence=coherence,
        high_level=high_level,
        context={
            "manifest_path": str(manifest) if manifest is not None else None,
            "repo_root": str(repo),
            "momentum_sample_count": len(samples),
        },
    )

    return snapshot

