"""Continuum Compass report parser and summary helpers.

This module ingests oracle-style payloads that describe the recommended
weight distribution for Echo's Continuum programs.  The light-weight data
structures make it easy for other packages (including documentation
renderers and CLIs) to surface consistent summaries without duplicating
parsing logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping, MutableMapping, Sequence

__all__ = [
    "WeightRecommendation",
    "ExpansionTarget",
    "StabilityScore",
    "ContinuumCompassReport",
    "parse_compass_payload",
]


_FLOAT_TOLERANCE = 1e-9


def _coerce_float(value: object, *, field: str) -> float:
    """Return *value* as ``float`` with a descriptive error on failure."""

    try:
        return float(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive branch
        raise TypeError(f"{field} must be numeric, received {value!r}") from exc


@dataclass(frozen=True, slots=True)
class WeightRecommendation:
    """A single weight recommendation for a Continuum initiative."""

    name: str
    current: float
    recommended: float
    rationale: str = ""

    @property
    def delta(self) -> float:
        """Return the signed delta between the recommended and current weight."""

        return self.recommended - self.current

    def direction(self) -> str:
        """Return a human friendly direction for the recommendation."""

        if self.delta > _FLOAT_TOLERANCE:
            return "increase"
        if self.delta < -_FLOAT_TOLERANCE:
            return "decrease"
        return "maintain"

    def render_summary(self) -> str:
        """Return a compact summary sentence for the recommendation."""

        direction = self.direction()
        symbol = {
            "increase": "↑",
            "decrease": "↓",
            "maintain": "→",
        }.get(direction, "→")
        if direction == "maintain":
            change = f"{symbol} hold at {self.current:.2f}"
        else:
            change = (
                f"{symbol} {direction} from {self.current:.2f} to {self.recommended:.2f}"
            )
        if self.rationale:
            return f"{self.name}: {change} ({self.rationale})"
        return f"{self.name}: {change}"


@dataclass(frozen=True, slots=True)
class ExpansionTarget:
    """An expansion target recommended by the oracle payload."""

    name: str
    recommended_weight: float
    reason: str = ""

    def render_summary(self) -> str:
        """Return a one-line description of the expansion target."""

        base = f"{self.name}: target {self.recommended_weight:.2f}"
        if self.reason:
            return f"{base} ({self.reason})"
        return base


@dataclass(frozen=True, slots=True)
class StabilityScore:
    """Observed and predicted stability scores for the current cycle."""

    current: float
    predicted: float
    method: str = ""

    @property
    def delta(self) -> float:
        """Return the predicted delta relative to the current score."""

        return self.predicted - self.current

    def render_summary(self) -> str:
        """Return a concise summary of the stability outlook."""

        delta = self.delta
        if delta > _FLOAT_TOLERANCE:
            trend = f"+{delta:.2f}"
        elif delta < -_FLOAT_TOLERANCE:
            trend = f"{delta:.2f}"
        else:
            trend = "±0.00"
        if self.method:
            return (
                f"Stability shifts {trend} (current {self.current:.2f} → {self.predicted:.2f};"
                f" via {self.method})"
            )
        return f"Stability shifts {trend} (current {self.current:.2f} → {self.predicted:.2f})"


@dataclass(slots=True)
class ContinuumCompassReport:
    """Structured representation of the oracle payload."""

    project: str
    owner: str
    generated_at: str | None
    source: str
    weights: Sequence[WeightRecommendation]
    expansion_targets: Sequence[ExpansionTarget]
    stability_score: StabilityScore

    def weight_adjustments(self) -> Sequence[WeightRecommendation]:
        """Return the weight recommendations sorted by absolute delta."""

        return tuple(
            sorted(
                self.weights,
                key=lambda item: (abs(item.delta), item.name.lower()),
                reverse=True,
            )
        )

    def render_summary_lines(self) -> List[str]:
        """Return a list of human-friendly summary lines."""

        lines = [f"Continuum Compass :: {self.project} (owner: {self.owner})"]
        if self.generated_at:
            lines.append(f"Generated at {self.generated_at} from {self.source or 'unknown source'}")
        elif self.source:
            lines.append(f"Source: {self.source}")

        if self.weights:
            lines.append("")
            lines.append("Weight adjustments:")
            for recommendation in self.weight_adjustments():
                lines.append(f"- {recommendation.render_summary()}")

        if self.expansion_targets:
            lines.append("")
            lines.append("Expansion targets:")
            for target in self.expansion_targets:
                lines.append(f"- {target.render_summary()}")

        lines.append("")
        lines.append(self.stability_score.render_summary())

        return lines

    def render_summary(self) -> str:
        """Return the formatted multi-line summary."""

        return "\n".join(self.render_summary_lines())


def parse_compass_payload(payload: Mapping[str, object]) -> ContinuumCompassReport:
    """Parse *payload* into a :class:`ContinuumCompassReport` instance."""

    project = str(payload.get("project", ""))
    owner = str(payload.get("owner", ""))
    generated_at = payload.get("generated_at")
    generated_at_str: str | None = None
    if generated_at is not None:
        generated_at_str = str(generated_at)
    source = str(payload.get("source", ""))

    raw_weights = payload.get("weights", {})
    weight_items: Iterable[tuple[str, Mapping[str, object]]]
    if isinstance(raw_weights, Mapping):
        weight_items = raw_weights.items()
    else:  # pragma: no cover - defensive branch
        raise TypeError("weights must be a mapping of name -> weight data")

    weights: list[WeightRecommendation] = []
    for name, data in weight_items:
        if not isinstance(data, Mapping):  # pragma: no cover - defensive branch
            raise TypeError(f"weight entry for {name!r} must be a mapping")
        mapping: MutableMapping[str, object] = dict(data)
        current = _coerce_float(mapping.get("current", 0.0), field=f"weights[{name}].current")
        recommended = _coerce_float(
            mapping.get("recommended", current),
            field=f"weights[{name}].recommended",
        )
        rationale = str(mapping.get("rationale", "")).strip()
        weights.append(
            WeightRecommendation(
                name=str(name),
                current=current,
                recommended=recommended,
                rationale=rationale,
            )
        )

    expansion_raw = payload.get("expansion_targets") or []
    if not isinstance(expansion_raw, Iterable):  # pragma: no cover - defensive branch
        raise TypeError("expansion_targets must be iterable")

    expansion_targets: list[ExpansionTarget] = []
    for item in expansion_raw:
        if not isinstance(item, Mapping):  # pragma: no cover - defensive branch
            raise TypeError("expansion target entries must be mappings")
        target_map: MutableMapping[str, object] = dict(item)
        name = str(target_map.get("name", ""))
        recommended_weight = _coerce_float(
            target_map.get("recommended_weight", 0.0),
            field=f"expansion_targets[{name}].recommended_weight",
        )
        reason = str(target_map.get("reason", "")).strip()
        expansion_targets.append(
            ExpansionTarget(name=name, recommended_weight=recommended_weight, reason=reason)
        )

    stability_map = dict(payload.get("stability_score") or {})
    current_score = _coerce_float(
        stability_map.get("current", 0.0),
        field="stability_score.current",
    )
    predicted_score = _coerce_float(
        stability_map.get("predicted", current_score),
        field="stability_score.predicted",
    )
    method = str(stability_map.get("method", "")).strip()
    stability = StabilityScore(current=current_score, predicted=predicted_score, method=method)

    return ContinuumCompassReport(
        project=project,
        owner=owner,
        generated_at=generated_at_str,
        source=source,
        weights=tuple(weights),
        expansion_targets=tuple(expansion_targets),
        stability_score=stability,
    )
