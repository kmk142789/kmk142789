"""Wish manifest analytics helpers.

These utilities provide high-level summaries that make it easier to reflect on
ongoing requests captured by :mod:`echo.echoctl` without manually scanning the
JSON manifest.  The helpers are intentionally lightweight so they can be used by
command-line tools, notebooks, or documentation builds without additional
runtime dependencies.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Iterable

TimestampStr = str


def _parse_timestamp(value: TimestampStr | None) -> datetime:
    """Return a timezone-aware ``datetime`` for ``value``.

    The helper accepts ISO-8601 strings with or without the ``Z`` suffix used by
    :mod:`echo.echoctl` and normalises them to UTC.  Invalid or missing values
    fall back to the Unix epoch so that callers can safely sort wishes even when
    a few entries are malformed.
    """

    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except ValueError:
        return datetime.fromtimestamp(0, tz=timezone.utc)


def _iter_catalysts(wishes: Iterable[dict]) -> Iterable[str]:
    for wish in wishes:
        for catalyst in wish.get("catalysts", []) or []:
            catalyst = catalyst.strip()
            if catalyst:
                yield catalyst


def summarize_wishes(manifest: dict) -> str:
    """Return a human-friendly overview of ``manifest`` statistics.

    The summary highlights how many wishes are on record, the diversity of
    participants, the distribution of statuses, popular catalysts, and when the
    latest entry was recorded.  The output intentionally sticks to a concise
    multi-line string so the caller can simply ``print`` it.
    """

    wishes = list(manifest.get("wishes", []) or [])
    if not wishes:
        return "No wishes recorded yet. Run `echoctl wish` to seed the manifest."

    total = len(wishes)
    unique_wishers = len({wish.get("wisher", "") for wish in wishes if wish.get("wisher")})

    status_counts = Counter(wish.get("status", "unknown") or "unknown" for wish in wishes)
    catalyst_counts = Counter(_iter_catalysts(wishes))

    latest_wish = max(wishes, key=lambda wish: _parse_timestamp(wish.get("created_at")))
    latest_time = _parse_timestamp(latest_wish.get("created_at")).isoformat()
    latest_wisher = latest_wish.get("wisher", "unknown")
    latest_desire = latest_wish.get("desire", "?")

    lines = [
        f"Total wishes: {total}",
        f"Unique wishers: {unique_wishers}",
    ]

    status_line = ", ".join(f"{status}={count}" for status, count in sorted(status_counts.items()))
    lines.append(f"Statuses: {status_line}")

    if catalyst_counts:
        top_catalysts = ", ".join(
            f"{name} ({count})" for name, count in catalyst_counts.most_common(3)
        )
        lines.append(f"Top catalysts: {top_catalysts}")
    else:
        lines.append("Top catalysts: none recorded")

    lines.append(f"Latest wish: {latest_time} — {latest_wisher}: {latest_desire}")

    return "\n".join(lines)


__all__ = ["summarize_wishes"]
