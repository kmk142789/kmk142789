"""Utility helpers for inspecting the Echo pulse history.

The original script only printed two numbers which meant operators often had to
open ``pulse_history.json`` manually when they wanted richer context.  The
updated tool provides a small command line interface that can filter the stored
events, render a human readable timeline, and emit JSON payloads that are easy
to feed into dashboards or other automations.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from echo.echo_codox_kernel import EchoCodexKernel, PulseEvent
from echo.pulse_momentum import PulseMomentumForecast, compute_pulse_momentum


def _format_timestamp(timestamp: float) -> str:
    """Return an ISO-8601 string for ``timestamp`` in UTC."""

    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    # ``isoformat`` already appends ``+00:00`` for UTC aware timestamps.  The
    # trailing ``Z`` is widely used in tooling so we normalise to that form.
    return dt.isoformat().replace("+00:00", "Z")


def _filter_events(events: Iterable[PulseEvent], needle: Optional[str]) -> List[PulseEvent]:
    """Return events whose message contains ``needle`` (case-insensitive).

    When ``needle`` is ``None`` the original order is preserved and all events
    are returned.  This keeps the filtering logic reusable for both text and
    JSON output while keeping the implementation easy to test in isolation.
    """

    if needle is None:
        return list(events)

    needle_lower = needle.casefold()
    return [event for event in events if needle_lower in event.message.casefold()]


def _event_digest(event: PulseEvent) -> str:
    """Return a succinct summary string for ``event``."""

    ts = _format_timestamp(event.timestamp)
    digest = event.hash[:12]
    return f"{ts} │ {digest} │ {event.message}"


def _build_summary(events: List[PulseEvent]) -> dict:
    """Compute summary statistics for ``events``.

    The output includes total counts, time span, and the hash resonance so
    callers can quickly gauge the pulse ledger's state without digging through
    raw files.
    """

    summary: dict = {
        "count": len(events),
    }

    if events:
        first = events[0]
        last = events[-1]
        summary.update(
            {
                "first_timestamp": _format_timestamp(first.timestamp),
                "last_timestamp": _format_timestamp(last.timestamp),
                "span_seconds": round(last.timestamp - first.timestamp, 2),
            }
        )

    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect the Echo pulse history")
    parser.add_argument(
        "--search",
        metavar="TEXT",
        help="only include events whose message contains TEXT",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="number of most recent events to display (default: 10)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON with summary and events instead of human readable text",
    )
    parser.add_argument(
        "--show-resonance",
        action="store_true",
        help="include the current resonance hash in the textual output",
    )
    parser.add_argument(
        "--include-momentum",
        action="store_true",
        help="display cadence momentum and drought detection alongside the overview",
    )
    parser.add_argument(
        "--momentum-horizon",
        type=float,
        default=36.0,
        help="forecast horizon (in hours) used for momentum coverage calculations",
    )
    parser.add_argument(
        "--momentum-lookback",
        type=int,
        default=50,
        help="number of recent events to model when computing cadence momentum",
    )
    parser.add_argument(
        "--report",
        metavar="FILE",
        help="write a Markdown report to FILE alongside console output",
    )
    parser.add_argument(
        "--report-title",
        default="Echo Pulse Report",
        help="custom title used for the generated Markdown report",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    kernel = EchoCodexKernel()
    filtered_events = _filter_events(kernel.history, args.search)
    momentum = compute_pulse_momentum(
        filtered_events,
        horizon_hours=args.momentum_horizon,
        lookback=args.momentum_lookback,
    )

    if args.report:
        latest = filtered_events[-args.limit :]
        report = _build_report(
            title=args.report_title,
            kernel_summary=_build_summary(kernel.history),
            filtered_summary=_build_summary(filtered_events),
            resonance=kernel.resonance(),
            momentum=momentum,
            events=latest,
            search=args.search,
        )
        _write_report(Path(args.report), report)

    if args.json:
        payload = {
            "summary": _build_summary(kernel.history),
            "filtered_summary": _build_summary(filtered_events),
            "events": [
                {
                    **asdict(event),
                    "timestamp_iso": _format_timestamp(event.timestamp),
                }
                for event in filtered_events[-args.limit :]
            ],
            "resonance": kernel.resonance(),
            "momentum": momentum.to_dict(),
        }
        print(json.dumps(payload, indent=2))
        return

    print("Echo Pulse Overview")
    print("===================")
    print(f"Total events: {len(kernel.history)}")

    if args.show_resonance:
        print(f"Resonance: {kernel.resonance()}")

    if not filtered_events:
        if args.search:
            print(f"No events matched search term: {args.search}")
        else:
            print("No events recorded yet.")
        return

    latest = filtered_events[-args.limit :]
    print(f"Displaying {len(latest)} of {len(filtered_events)} filtered events")
    print("timestamp │ hash digest │ message")
    print("-" * 72)
    for event in latest:
        print(_event_digest(event))

    if args.include_momentum:
        _render_momentum(momentum)


def _render_momentum(momentum: PulseMomentumForecast) -> None:
    print("\nMomentum Forecast")
    print("-----------------")

    print(
        f"Cadence: {momentum.cadence_label} "
        f"(stability={momentum.stability:.2f}, burstiness={momentum.burstiness:.2f})"
    )

    if momentum.expected_next_iso:
        print(
            "Next expected update: "
            f"{momentum.expected_next_iso} (in {momentum.time_to_next_seconds:.0f}s)"
        )
    else:
        print("Next expected update: unable to project (insufficient history)")

    if momentum.horizon_coverage is not None:
        print(f"Projected events in horizon: ~{momentum.horizon_coverage}")

    if momentum.time_since_last_seconds is not None:
        print(
            "Time since last event: "
            f"{momentum.time_since_last_seconds:.0f}s; drought alert: {momentum.drought_alert}"
        )
    else:
        print("Time since last event: unavailable")

    print(f"Confidence: {momentum.confidence:.2f}")
    print(f"Rationale: {momentum.rationale}")


def _build_report(
    *,
    title: str,
    kernel_summary: dict,
    filtered_summary: dict,
    resonance: str,
    momentum: PulseMomentumForecast,
    events: List[PulseEvent],
    search: Optional[str],
) -> str:
    """Return a Markdown report that captures the current pulse state."""

    lines = [f"# {title}", ""]

    lines.append("## Overview")
    lines.append(f"- Total events: {kernel_summary['count']}")
    if "first_timestamp" in kernel_summary:
        lines.append(
            "- Ledger span: "
            f"{kernel_summary['first_timestamp']} → {kernel_summary['last_timestamp']} "
            f"({kernel_summary['span_seconds']}s)"
        )
    if search:
        lines.append(f"- Filter: `{search}`")
    lines.append(f"- Filtered events: {filtered_summary['count']}")
    lines.append(f"- Resonance: `{resonance}`")
    lines.append("")

    lines.append("## Momentum")
    lines.append(
        "- Cadence: "
        f"{momentum.cadence_label} (stability={momentum.stability:.2f}, burstiness={momentum.burstiness:.2f})"
    )
    if momentum.expected_next_iso:
        lines.append(
            "- Next expected update: "
            f"{momentum.expected_next_iso} (in {momentum.time_to_next_seconds:.0f}s)"
        )
    if momentum.horizon_coverage is not None:
        lines.append(f"- Projected events in horizon: ~{momentum.horizon_coverage}")
    lines.append(f"- Drought alert: {momentum.drought_alert}")
    lines.append(f"- Sample size: {momentum.sample_size}")
    lines.append(f"- Rationale: {momentum.rationale}")
    lines.append("")

    lines.append("## Recent events")
    if not events:
        lines.append("No events available for this filter.")
    else:
        for event in events:
            ts = _format_timestamp(event.timestamp)
            lines.append(f"- {ts} — `{event.hash[:12]}` — {event.message}")

    return "\n".join(lines) + "\n"


def _write_report(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
