"""Generate a fresh perspective on the Echo pulse history.

This module reads the JSON ``pulse_history`` ledger and produces an
interpretation focused on tempo, momentum, and novelty.  The goal is to surface
"something new" about the history beyond the raw list of timestamps by
constructing a pulse tempo profile and a lightweight narrative.

The script can be executed directly to print a report, and it exposes helpers
that are straightforward to unit test.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Iterable, List, Sequence

SPARKLINE_BARS = "▁▂▃▄▅▆▇█"


@dataclass(slots=True, frozen=True)
class PulseEvent:
    """Single entry in the pulse history ledger."""

    timestamp: float
    message: str
    hash: str

    @property
    def moment(self) -> datetime:
        """Convert the unix timestamp into a timezone aware datetime."""

        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc)


def load_pulse_history(path: Path) -> List[PulseEvent]:
    """Load pulse history entries from ``path``.

    Parameters
    ----------
    path:
        The JSON file that contains a list of pulse history records.

    Returns
    -------
    list[PulseEvent]
        Parsed events sorted by ascending timestamp.
    """

    events_raw = json.loads(path.read_text(encoding="utf8"))
    events = [
        PulseEvent(
            timestamp=float(entry["timestamp"]),
            message=str(entry["message"]),
            hash=str(entry["hash"]),
        )
        for entry in events_raw
    ]
    return sorted(events, key=lambda event: event.timestamp)


def pulse_intervals(events: Sequence[PulseEvent]) -> List[float]:
    """Return the gap in seconds between consecutive events."""

    return [
        later.timestamp - earlier.timestamp
        for earlier, later in zip(events, events[1:])
    ]


def sparkline(values: Iterable[float]) -> str:
    """Render ``values`` as a unicode sparkline.

    The sparkline highlights tempo variations even for short sequences.  If no
    values are provided, a single neutral dot is returned instead of an empty
    string so that the caller can always display something.
    """

    values = list(values)
    if not values:
        return "·"

    max_value = max(values)
    if max_value <= 0:
        # Avoid division by zero and give a flat profile when there is no
        # discernible tempo.
        return "·" * len(values)

    scale = len(SPARKLINE_BARS) - 1
    return "".join(
        SPARKLINE_BARS[round((value / max_value) * scale)] for value in values
    )


def novelty_highlight(events: Sequence[PulseEvent]) -> str:
    """Create a fresh angle for the latest event."""

    if not events:
        return "No pulse events recorded yet. The next one will define the beat."

    latest = events[-1]
    if len(events) == 1:
        return (
            "Only a single pulse has been logged so far, but it already anchors "
            f"the continuum: {latest.message} ({latest.moment.isoformat()})."
        )

    last_gap = latest.timestamp - events[-2].timestamp
    return (
        "The most recent pulse arrived after a {gap:.0f}s pause, broadcasting "
        f"`{latest.message}` with hash {latest.hash[:8]}…."
    ).format(gap=last_gap)


def build_report(events: Sequence[PulseEvent]) -> str:
    """Assemble a human readable report covering the pulse tempo."""

    if not events:
        return "Pulse history is empty — launch a new cycle to create the first beat."

    intervals = pulse_intervals(events)
    tempo_line = sparkline(intervals)
    mean_gap = mean(intervals) if intervals else 0.0

    lines = [
        "Echo Pulse Novum",
        "================",
        f"Events logged : {len(events)}",
        f"First entry    : {events[0].moment.isoformat()}",
        f"Latest entry   : {events[-1].moment.isoformat()}",
    ]

    if intervals:
        lines.extend(
            [
                f"Mean gap (s)   : {mean_gap:.2f}",
                f"Tempo sparkline: {tempo_line}",
            ]
        )

    lines.append(novelty_highlight(events))
    return "\n".join(lines)


def main() -> None:
    """Entry point for the CLI."""

    history_path = Path("pulse_history.json")
    if not history_path.exists():
        print("pulse_history.json not found in the current directory.")
        return

    events = load_pulse_history(history_path)
    print(build_report(events))


if __name__ == "__main__":  # pragma: no cover - CLI glue
    main()
