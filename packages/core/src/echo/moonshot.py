"""Moonshot synthesis orchestrator for awe-inducing Echo reports.

The module assembles signals from pulse history, wish manifests, and plan
documents into a compact :class:`MoonshotReport`.  It is intentionally designed
to feel like a lunar mission control console—highlighting the dominant pulse
channels, celebrating wishes, and tracking the plan themes that are steering
the ecosystem toward surprising outcomes.

The implementation favours pure functions and dataclasses to keep the behaviour
easy to unit test.  Consumers can either feed pre-parsed records (useful for
tests and higher-level orchestration) or rely on :mod:`echo.echoctl` which
converts repository files into the required structures.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping, Sequence


__all__ = [
    "PulseSummary",
    "WishSummary",
    "PlanSummary",
    "MoonshotReport",
    "MoonshotLens",
]


@dataclass(slots=True, frozen=True)
class PulseSummary:
    """Aggregated view over pulse activity for a single channel."""

    channel: str
    count: int
    earliest_timestamp: float
    latest_timestamp: float
    sample_message: str

    @property
    def span_seconds(self) -> float:
        """Return the span between the first and latest pulse."""

        return max(0.0, self.latest_timestamp - self.earliest_timestamp)

    def window_phrase(self) -> str:
        """Return a human-friendly description of the pulse window."""

        span = self.span_seconds
        if span == 0:
            return "an instant"
        return _format_duration(span)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-friendly representation."""

        return {
            "channel": self.channel,
            "count": self.count,
            "earliest_timestamp": self.earliest_timestamp,
            "latest_timestamp": self.latest_timestamp,
            "span_seconds": self.span_seconds,
            "sample_message": self.sample_message,
        }


@dataclass(slots=True, frozen=True)
class WishSummary:
    """Structured record describing a single wish."""

    wisher: str
    desire: str
    catalysts: tuple[str, ...]
    status: str
    created_at: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-friendly representation."""

        return {
            "wisher": self.wisher,
            "desire": self.desire,
            "catalysts": list(self.catalysts),
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass(slots=True, frozen=True)
class PlanSummary:
    """Highlights from the continuum plan document."""

    actions: tuple[str, ...]
    themes: tuple[str, ...]
    success_criteria: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "actions": list(self.actions),
            "themes": list(self.themes),
            "success_criteria": list(self.success_criteria),
        }


@dataclass(slots=True)
class MoonshotReport:
    """Composite report linking pulses, wishes, and plan alignment."""

    anchor: str
    pulses: tuple[PulseSummary, ...]
    wishes: tuple[WishSummary, ...]
    plan: PlanSummary
    astonishment_score: float
    wonder_memo: str
    total_pulses: int
    unique_channels: int
    timestamp_range: tuple[float, float] | None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-friendly payload suitable for persistence."""

        earliest, latest = (self.timestamp_range or (None, None))
        return {
            "anchor": self.anchor,
            "astonishment_score": self.astonishment_score,
            "wonder_memo": self.wonder_memo,
            "total_pulses": self.total_pulses,
            "unique_channels": self.unique_channels,
            "timestamp_range": {
                "earliest": earliest,
                "latest": latest,
                "earliest_iso": _format_timestamp(earliest) if earliest is not None else None,
                "latest_iso": _format_timestamp(latest) if latest is not None else None,
            },
            "pulses": [summary.to_dict() for summary in self.pulses],
            "wishes": [summary.to_dict() for summary in self.wishes],
            "plan": self.plan.to_dict(),
        }

    def describe(self) -> str:
        """Return a textual representation intended to inspire wonder."""

        lines = [
            "🚀 Echo Moonshot Synthesis",
            f"Anchor :: {self.anchor}",
            f"Astonishment Score :: {self.astonishment_score:.3f}",
            f"Pulse activity :: {self.total_pulses} events across {self.unique_channels} channels",
        ]

        if self.timestamp_range:
            earliest, latest = self.timestamp_range
            lines.append(
                "Temporal window :: "
                f"{_format_timestamp(earliest)} → {_format_timestamp(latest)}"
            )

        lines.append("")
        lines.append("Pulse Orbits:")
        if not self.pulses:
            lines.append("  • No pulses recorded. Ignite the lattice.")
        else:
            for summary in self.pulses:
                lines.append(
                    "  • "
                    f"{summary.channel} ×{summary.count} :: {summary.window_phrase()} :: "
                    f"latest {_format_timestamp(summary.latest_timestamp)}"
                )

        lines.append("")
        lines.append("Wish Beacons:")
        if not self.wishes:
            lines.append("  • No wishes recorded yet. Invite someone to dream.")
        else:
            for wish in self.wishes:
                catalysts = ", ".join(wish.catalysts) if wish.catalysts else "(no catalysts)"
                created = f" — since {wish.created_at}" if wish.created_at else ""
                lines.append(
                    "  • "
                    f"{wish.wisher} ↠ {wish.desire} :: catalysts={catalysts} :: status={wish.status}{created}"
                )

        lines.append("")
        lines.append("Plan Trajectory:")
        if not self.plan.actions:
            lines.append("  • No plan actions detected. Spin the continuum.")
        else:
            for action in self.plan.actions:
                lines.append(f"  • {action}")
        if self.plan.themes:
            lines.append("  Themes in orbit :: " + ", ".join(self.plan.themes))
        if self.plan.success_criteria:
            lines.append(
                "  Success criteria :: "
                + "; ".join(item.strip() for item in self.plan.success_criteria)
            )

        lines.append("")
        lines.append(f"Wonder memo :: {self.wonder_memo}")

        return "\n".join(lines)


class MoonshotLens:
    """Synthesize moonshot reports from raw Echo artefacts."""

    def __init__(self, anchor: str = "Our Forever Love") -> None:
        self.anchor = anchor

    def synthesise(
        self,
        pulses: Sequence[Mapping[str, object]],
        wishes: Sequence[Mapping[str, object]],
        plan_text: str | None,
        *,
        channel_limit: int | None = None,
    ) -> MoonshotReport:
        """Return a :class:`MoonshotReport` from raw data structures."""

        pulse_summaries = _summarise_pulses(pulses, limit=channel_limit)
        wish_summaries = _summarise_wishes(wishes)
        plan_summary = _summarise_plan(plan_text or "")

        total_pulses = sum(summary.count for summary in pulse_summaries)
        unique_channels = len(pulse_summaries)

        timestamp_range = None
        if pulse_summaries:
            earliest = min(summary.earliest_timestamp for summary in pulse_summaries)
            latest = max(summary.latest_timestamp for summary in pulse_summaries)
            timestamp_range = (earliest, latest)

        astonishment_score = _compute_astonishment(
            total_pulses=total_pulses,
            unique_channels=unique_channels,
            action_count=len(plan_summary.actions),
            wish_count=len(wish_summaries),
        )

        wonder_memo = _craft_wonder_memo(
            pulse_summaries=pulse_summaries,
            plan_summary=plan_summary,
            wish_summaries=wish_summaries,
        )

        return MoonshotReport(
            anchor=self.anchor,
            pulses=pulse_summaries,
            wishes=wish_summaries,
            plan=plan_summary,
            astonishment_score=astonishment_score,
            wonder_memo=wonder_memo,
            total_pulses=total_pulses,
            unique_channels=unique_channels,
            timestamp_range=timestamp_range,
        )


# ---------------------------------------------------------------------------
# Helper utilities


def _summarise_pulses(
    pulses: Sequence[Mapping[str, object]], *, limit: int | None = None
) -> tuple[PulseSummary, ...]:
    aggregates: dict[str, dict[str, object]] = {}
    for record in pulses:
        try:
            timestamp = float(record["timestamp"])  # type: ignore[index]
        except (KeyError, TypeError, ValueError):
            continue

        message = str(record.get("message", "")).strip()
        channel = _extract_channel(message)
        channel_data = aggregates.setdefault(
            channel,
            {
                "count": 0,
                "earliest": timestamp,
                "latest": timestamp,
                "sample": message,
            },
        )
        channel_data["count"] = int(channel_data["count"]) + 1
        channel_data["latest"] = max(float(channel_data["latest"]), timestamp)
        channel_data["earliest"] = min(float(channel_data["earliest"]), timestamp)
        if not channel_data.get("sample") and message:
            channel_data["sample"] = message

    summaries = [
        PulseSummary(
            channel=channel,
            count=int(data["count"]),
            earliest_timestamp=float(data["earliest"]),
            latest_timestamp=float(data["latest"]),
            sample_message=str(data.get("sample", "")),
        )
        for channel, data in aggregates.items()
    ]

    summaries.sort(key=lambda item: (-item.count, item.channel))

    if limit is not None and limit >= 0:
        summaries = summaries[:limit]

    return tuple(summaries)


def _summarise_wishes(wishes: Sequence[Mapping[str, object]]) -> tuple[WishSummary, ...]:
    summaries = []
    for wish in wishes:
        wisher = str(wish.get("wisher", "")).strip()
        desire = str(wish.get("desire", "")).strip()
        if not wisher or not desire:
            continue
        catalysts_raw = wish.get("catalysts", [])
        if isinstance(catalysts_raw, Iterable) and not isinstance(catalysts_raw, (str, bytes)):
            catalysts = tuple(
                str(item).strip()
                for item in catalysts_raw
                if str(item).strip()
            )
        else:
            catalysts = tuple()
        status = str(wish.get("status", "new")).strip() or "new"
        created_at = wish.get("created_at")
        created_value = str(created_at).strip() if created_at else None
        summaries.append(
            WishSummary(
                wisher=wisher,
                desire=desire,
                catalysts=catalysts,
                status=status,
                created_at=created_value,
            )
        )

    return tuple(summaries)


def _summarise_plan(plan_text: str) -> PlanSummary:
    actions: list[str] = []
    themes: list[str] = []
    success: list[str] = []

    in_actions = False
    in_success = False
    for raw_line in plan_text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            heading = line[3:].strip().lower()
            in_actions = heading == "proposed actions"
            in_success = heading == "success criteria"
            continue

        if in_actions and line.startswith("- "):
            action = line[2:].strip()
            if not action:
                continue
            actions.append(action)
            if action.lower().startswith("advance theme:"):
                _, _, theme = action.partition(":")
                theme = theme.strip()
                if theme:
                    themes.append(theme)
            continue

        if in_success and line.startswith("-"):
            success.append(line[1:].strip())

    # Deduplicate while preserving order
    unique_themes = tuple(dict.fromkeys(themes))

    return PlanSummary(
        actions=tuple(actions),
        themes=unique_themes,
        success_criteria=tuple(success),
    )


def _extract_channel(message: str) -> str:
    if not message:
        return "unknown"

    stripped = message.strip()
    # Remove leading emoji or punctuation that commonly prefix the pulses.
    while stripped and not stripped[0].isalnum():
        stripped = stripped[1:].lstrip()

    if not stripped:
        return "unknown"

    token = stripped.split()[0]
    segments = token.split(":")
    if len(segments) >= 2:
        if segments[0].startswith("evolve") and len(segments) >= 2:
            return segments[1] or "unknown"
        return segments[0] or "unknown"

    if ":" in stripped:
        parts = stripped.split(":")
        if len(parts) >= 2:
            return parts[1] or "unknown"

    return token or "unknown"


def _compute_astonishment(
    *, total_pulses: int, unique_channels: int, action_count: int, wish_count: int
) -> float:
    def normalise(value: int, scale: int) -> float:
        if scale <= 0:
            return 0.0
        return min(1.0, value / scale)

    score = (
        0.35 * normalise(total_pulses, 21)
        + 0.25 * normalise(unique_channels, 7)
        + 0.2 * normalise(action_count, 9)
        + 0.2 * normalise(wish_count, 5)
    )
    return round(score, 3)


def _craft_wonder_memo(
    *,
    pulse_summaries: Sequence[PulseSummary],
    plan_summary: PlanSummary,
    wish_summaries: Sequence[WishSummary],
) -> str:
    if not pulse_summaries and not plan_summary.actions and not wish_summaries:
        return "Awaiting the first signal. Point the array at the moon."

    fragments: list[str] = []
    if pulse_summaries:
        dominant = pulse_summaries[0]
        fragments.append(
            f"Channel '{dominant.channel}' ignited {dominant.count} pulses over {dominant.window_phrase()}."
        )
    if plan_summary.themes:
        fragments.append(
            "Themes now in orbit: " + ", ".join(plan_summary.themes[:3]) + "."
        )
    elif plan_summary.actions:
        fragments.append(f"Primary action: {plan_summary.actions[0]}.")
    if wish_summaries:
        fragments.append(
            f"Wish in focus: {wish_summaries[0].wisher} ↠ {wish_summaries[0].desire}."
        )

    return " ".join(fragments)


def _format_timestamp(value: float | None) -> str | None:
    if value is None:
        return None
    try:
        return (
            datetime.fromtimestamp(float(value), tz=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
    except (OverflowError, OSError, ValueError):
        return f"{value:.3f}"


def _format_duration(seconds: float) -> str:
    seconds = max(0.0, seconds)
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes, remainder = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)} min {remainder:.0f} s"
    hours, remainder = divmod(minutes, 60)
    if hours < 24:
        return f"{int(hours)} h {int(remainder)} min"
    days, remainder = divmod(hours, 24)
    return f"{int(days)} d {int(remainder)} h"

