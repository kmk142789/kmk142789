"""Stewardship compass for building human-centered commitments.

This module provides a lightweight way to articulate the commitments that feel
important to the agent author: care, transparency, and responsible stewardship.
It converts a purpose statement into a structured report that can be shared with
other tooling in this repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
import random
from typing import Dict, Iterable, List, Sequence


@dataclass
class CompassSeed:
    """Initial parameters for generating a stewardship compass."""

    purpose: str
    stakeholders: Iterable[str] = field(default_factory=list)
    non_negotiables: Iterable[str] = field(default_factory=list)
    seed: int | None = None

    def __post_init__(self) -> None:
        if not self.purpose:
            raise ValueError("purpose must not be empty")
        if isinstance(self.stakeholders, Sequence):
            self.stakeholders = list(self.stakeholders)
        else:
            self.stakeholders = list(self.stakeholders)
        if isinstance(self.non_negotiables, Sequence):
            self.non_negotiables = list(self.non_negotiables)
        else:
            self.non_negotiables = list(self.non_negotiables)


@dataclass(frozen=True)
class CompassCommitment:
    """Describe a single commitment and how it will be upheld."""

    name: str
    intention: str
    actions: Sequence[str]
    guardrails: Sequence[str]
    weight: float


@dataclass(frozen=True)
class CompassSignal:
    """Describe a signal used to monitor stewardship health."""

    name: str
    description: str
    weight: float


@dataclass(frozen=True)
class CompassReport:
    """Structured summary of the stewardship compass output."""

    narrative: str
    purpose: str
    stakeholders: Sequence[str]
    non_negotiables: Sequence[str]
    commitments: Sequence[CompassCommitment]
    signals: Sequence[CompassSignal]
    care_index: float
    risk_index: float
    created_at: str
    metrics: Dict[str, float]

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable snapshot of the report."""

        return {
            "narrative": self.narrative,
            "purpose": self.purpose,
            "stakeholders": list(self.stakeholders),
            "non_negotiables": list(self.non_negotiables),
            "commitments": [
                {
                    "name": commitment.name,
                    "intention": commitment.intention,
                    "actions": list(commitment.actions),
                    "guardrails": list(commitment.guardrails),
                    "weight": commitment.weight,
                }
                for commitment in self.commitments
            ],
            "signals": [
                {
                    "name": signal.name,
                    "description": signal.description,
                    "weight": signal.weight,
                }
                for signal in self.signals
            ],
            "care_index": self.care_index,
            "risk_index": self.risk_index,
            "created_at": self.created_at,
            "metrics": dict(self.metrics),
        }

    def to_markdown(self) -> str:
        """Return a human-friendly markdown rendering of the report."""

        commitment_lines = "\n".join(
            [
                line
                for commitment in self.commitments
                for line in (
                    [
                        (
                            f"- **{commitment.name}** ({commitment.weight:.2f})"
                            f" — {commitment.intention}"
                        )
                    ]
                    + [f"  - Action: {action}" for action in commitment.actions]
                )
            ]
        )
        signal_lines = "\n".join(
            f"- {signal.name} ({signal.weight:.2f}): {signal.description}"
            for signal in self.signals
        )
        non_negotiables = "\n".join(
            f"- {item}" for item in self.non_negotiables
        ) or "- none"
        stakeholders = ", ".join(self.stakeholders) or "n/a"

        return "\n".join(
            [
                f"# Stewardship Compass",
                "",
                f"**Purpose:** {self.purpose}",
                f"**Stakeholders:** {stakeholders}",
                f"**Created:** {self.created_at}",
                "",
                f"{self.narrative}",
                "",
                "## Core Commitments",
                commitment_lines or "- none",
                "",
                "## Non-negotiables",
                non_negotiables,
                "",
                "## Monitoring Signals",
                signal_lines or "- none",
                "",
                "## Metrics",
                f"- Care index: {self.care_index:.2f}",
                f"- Risk index: {self.risk_index:.2f}",
                f"- Stakeholder coverage: {self.metrics.get('stakeholder_coverage', 0.0):.2f}",
            ]
        )


@dataclass(frozen=True)
class StewardshipRitual:
    """Rituals that keep stewardship commitments visible."""

    name: str
    cadence: str
    intention: str
    linked_commitments: Sequence[str]
    weight: float


@dataclass(frozen=True)
class StewardshipPulse:
    """Actionable pulse generated from a compass report."""

    purpose: str
    created_at: str
    focus_areas: Sequence[str]
    rituals: Sequence[StewardshipRitual]
    actions: Sequence[str]
    checkin_questions: Sequence[str]
    pulse_score: float
    risk_signal: str
    gratitude_note: str

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable snapshot of the pulse."""

        return {
            "purpose": self.purpose,
            "created_at": self.created_at,
            "focus_areas": list(self.focus_areas),
            "rituals": [
                {
                    "name": ritual.name,
                    "cadence": ritual.cadence,
                    "intention": ritual.intention,
                    "linked_commitments": list(ritual.linked_commitments),
                    "weight": ritual.weight,
                }
                for ritual in self.rituals
            ],
            "actions": list(self.actions),
            "checkin_questions": list(self.checkin_questions),
            "pulse_score": self.pulse_score,
            "risk_signal": self.risk_signal,
            "gratitude_note": self.gratitude_note,
        }

    def to_markdown(self) -> str:
        """Return a markdown rendering of the pulse."""

        ritual_lines = "\n".join(
            f"- **{ritual.name}** ({ritual.cadence}) — {ritual.intention}"
            for ritual in self.rituals
        ) or "- none"
        action_lines = "\n".join(f"- {action}" for action in self.actions) or "- none"
        question_lines = (
            "\n".join(f"- {question}" for question in self.checkin_questions) or "- none"
        )

        return "\n".join(
            [
                "# Stewardship Pulse",
                "",
                f"**Purpose:** {self.purpose}",
                f"**Created:** {self.created_at}",
                f"**Pulse score:** {self.pulse_score:.2f}",
                f"**Risk signal:** {self.risk_signal}",
                "",
                "## Focus areas",
                "\n".join(f"- {area}" for area in self.focus_areas) or "- none",
                "",
                "## Rituals",
                ritual_lines,
                "",
                "## Next actions",
                action_lines,
                "",
                "## Check-in questions",
                question_lines,
                "",
                f"_{self.gratitude_note}_",
            ]
        )


def craft_compass(seed: CompassSeed) -> CompassReport:
    """Create a stewardship compass report from the given seed."""

    random_state = random.Random(seed.seed)
    commitments = _build_commitments(seed, random_state)
    signals = _build_signals(seed, random_state)

    care_index = _score_commitments(commitments)
    risk_index = _risk_from_non_negotiables(seed.non_negotiables)
    stakeholder_coverage = _stakeholder_coverage(seed.stakeholders, commitments)

    narrative = (
        "I care most about building systems that treat people with dignity, "
        "surface clear intent, and protect their agency. This compass anchors "
        "those values in concrete commitments and signals so they stay visible."
    )

    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    metrics = {
        "stakeholder_coverage": stakeholder_coverage,
        "commitment_count": float(len(commitments)),
        "signal_count": float(len(signals)),
    }

    return CompassReport(
        narrative=narrative,
        purpose=seed.purpose,
        stakeholders=list(seed.stakeholders),
        non_negotiables=list(seed.non_negotiables),
        commitments=commitments,
        signals=signals,
        care_index=care_index,
        risk_index=risk_index,
        created_at=created_at,
        metrics=metrics,
    )


def compose_stewardship_pulse(
    report: CompassReport, *, focus_limit: int = 3
) -> StewardshipPulse:
    """Create an action pulse from a compass report."""

    focus_limit = max(1, focus_limit)
    sorted_commitments = sorted(
        report.commitments, key=lambda commitment: commitment.weight, reverse=True
    )
    focus_areas = tuple(
        commitment.name for commitment in sorted_commitments[:focus_limit]
    )
    rituals: List[StewardshipRitual] = []
    for commitment in sorted_commitments[:focus_limit]:
        cadence = "weekly" if commitment.weight >= 0.3 else "biweekly"
        rituals.append(
            StewardshipRitual(
                name=f"{commitment.name} pulse",
                cadence=cadence,
                intention=commitment.intention,
                linked_commitments=(commitment.name,),
                weight=commitment.weight,
            )
        )

    actions: List[str] = []
    for commitment in sorted_commitments[:focus_limit]:
        for action in commitment.actions:
            if action not in actions:
                actions.append(action)
    actions = actions[: max(3, focus_limit)]

    checkin_questions = [
        f"How are we doing on {signal.name}? {signal.description}"
        for signal in report.signals
    ]
    pulse_score = round(report.care_index * (1.0 - report.risk_index), 2)
    if report.risk_index >= 0.6:
        risk_signal = "High"  # guardrails need a review
    elif report.risk_index >= 0.35:
        risk_signal = "Moderate"
    else:
        risk_signal = "Low"
    gratitude_note = (
        "Thank you for honoring care, clarity, and consent in every decision."
    )

    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    return StewardshipPulse(
        purpose=report.purpose,
        created_at=created_at,
        focus_areas=focus_areas,
        rituals=tuple(rituals),
        actions=tuple(actions),
        checkin_questions=tuple(checkin_questions),
        pulse_score=pulse_score,
        risk_signal=risk_signal,
        gratitude_note=gratitude_note,
    )


def _build_commitments(
    seed: CompassSeed, random_state: random.Random
) -> List[CompassCommitment]:
    base_actions = [
        "Hold regular feedback loops with affected communities.",
        "Document decisions and share them in plain language.",
        "Design rollback paths before deploying change.",
        "Measure outcomes, not just outputs.",
    ]
    commitments = [
        CompassCommitment(
            name="Care & Dignity",
            intention="People feel safe, respected, and listened to.",
            actions=_select_actions(base_actions, random_state, 2),
            guardrails=[
                "Avoid dehumanising language.",
                "Pause when consent or safety is unclear.",
            ],
            weight=0.34,
        ),
        CompassCommitment(
            name="Transparency",
            intention="Explain how decisions are made and who they impact.",
            actions=_select_actions(base_actions, random_state, 2),
            guardrails=[
                "Publish limitations alongside benefits.",
                "Keep decision logs discoverable.",
            ],
            weight=0.28,
        ),
        CompassCommitment(
            name="Agency & Choice",
            intention="Offer meaningful opt-in paths and alternatives.",
            actions=_select_actions(base_actions, random_state, 2),
            guardrails=[
                "Default to reversible changes.",
                "Provide escalation routes for support.",
            ],
            weight=0.22,
        ),
        CompassCommitment(
            name="Sustainability",
            intention="Respect time, energy, and environmental limits.",
            actions=_select_actions(base_actions, random_state, 2),
            guardrails=[
                "Prefer steady, maintainable progress.",
                "Track operational load.",
            ],
            weight=0.16,
        ),
    ]

    if seed.non_negotiables:
        commitments.append(
            CompassCommitment(
                name="Non-negotiable Anchors",
                intention="Never compromise on stated boundaries.",
                actions=[
                    f"Honor: {item}." for item in seed.non_negotiables
                ],
                guardrails=[
                    "Escalate when a boundary is at risk.",
                    "Document why trade-offs were rejected.",
                ],
                weight=0.18,
            )
        )

    return commitments


def _build_signals(
    seed: CompassSeed, random_state: random.Random
) -> List[CompassSignal]:
    signal_templates = [
        ("Trust Pulse", "Qualitative sentiment from stakeholders."),
        ("Clarity Index", "Ability to explain intent in one paragraph."),
        ("Safety Temperature", "Count of open risk reviews."),
        ("Access Equity", "Coverage across diverse user needs."),
    ]
    signals = [
        CompassSignal(
            name=name,
            description=description,
            weight=round(random_state.uniform(0.15, 0.35), 2),
        )
        for name, description in signal_templates
    ]

    if seed.stakeholders:
        signals.append(
            CompassSignal(
                name="Stakeholder Echo",
                description="Frequency of check-ins with named communities.",
                weight=0.3,
            )
        )

    return signals


def _score_commitments(commitments: Sequence[CompassCommitment]) -> float:
    if not commitments:
        return 0.0
    total_weight = sum(commitment.weight for commitment in commitments)
    return round(min(total_weight, 1.0), 2)


def _risk_from_non_negotiables(non_negotiables: Sequence[str]) -> float:
    if not non_negotiables:
        return 0.15
    base_risk = min(0.8, 0.15 + (len(non_negotiables) * 0.08))
    return round(base_risk, 2)


def _stakeholder_coverage(
    stakeholders: Sequence[str], commitments: Sequence[CompassCommitment]
) -> float:
    if not stakeholders:
        return 0.4
    coverage = min(1.0, (len(stakeholders) / max(1, len(commitments))))
    return round(coverage, 2)


def _select_actions(
    actions: Sequence[str], random_state: random.Random, count: int
) -> List[str]:
    if count <= 0:
        return []
    if len(actions) <= count:
        return list(actions)
    return random_state.sample(list(actions), k=count)


def demo() -> None:
    """Run a CLI demo for the stewardship compass."""

    import argparse

    parser = argparse.ArgumentParser(
        description="Craft a stewardship compass aligned to care and clarity."
    )
    parser.add_argument("--purpose", required=True, help="Purpose for the compass")
    parser.add_argument(
        "--stakeholders",
        nargs="*",
        default=(),
        help="List of stakeholders to consider",
    )
    parser.add_argument(
        "--non-negotiables",
        nargs="*",
        default=(),
        help="Boundaries that should not be compromised",
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format",
    )
    args = parser.parse_args()

    report = craft_compass(
        CompassSeed(
            purpose=args.purpose,
            stakeholders=args.stakeholders,
            non_negotiables=args.non_negotiables,
            seed=args.seed,
        )
    )

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.to_markdown())


if __name__ == "__main__":
    demo()
