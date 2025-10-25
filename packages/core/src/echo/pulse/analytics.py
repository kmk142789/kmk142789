"""Analytics helpers for the Echo pulse ledger."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from .ledger import PulseLedger, PulseReceipt

__all__ = [
    "PulseSummary",
    "summarize_receipts",
    "summarize_ledger",
    "render_summary_table",
]


@dataclass(frozen=True)
class PulseSummary:
    """Condensed view of activity stored in the pulse ledger."""

    total_receipts: int
    unique_actors: tuple[str, ...]
    actor_counts: Mapping[str, int]
    result_counts: Mapping[str, int]
    seeds: tuple[str, ...]
    latest_time: datetime | None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation of the summary."""

        latest = self.latest_time.isoformat() if self.latest_time else None
        return {
            "total_receipts": self.total_receipts,
            "unique_actors": list(self.unique_actors),
            "actor_counts": dict(self.actor_counts),
            "result_counts": dict(self.result_counts),
            "seeds": list(self.seeds),
            "latest_time": latest,
        }


def summarize_receipts(receipts: Iterable["PulseReceipt"]) -> PulseSummary:
    """Build a :class:`PulseSummary` from *receipts*.

    The receipts may be provided in any iterable order.  Actor and result counts
    are arranged in descending frequency to highlight the most active entries
    first.
    """

    serialised = list(receipts)
    total = len(serialised)

    actor_counter: Counter[str] = Counter()
    result_counter: Counter[str] = Counter()
    seeds: list[str] = []
    seen_seeds: set[str] = set()
    timestamps: list[datetime] = []

    for receipt in serialised:
        actor_counter.update([receipt.actor])
        result_counter.update([receipt.result])
        if receipt.seed not in seen_seeds:
            seen_seeds.add(receipt.seed)
            seeds.append(receipt.seed)
        parsed = _parse_time(receipt.time)
        if parsed is not None:
            timestamps.append(parsed)

    actor_counts = MappingProxyType(dict(actor_counter.most_common()))
    result_counts = MappingProxyType(dict(result_counter.most_common()))
    unique_actors = tuple(actor_counts.keys())
    latest_time = max(timestamps) if timestamps else None

    return PulseSummary(
        total_receipts=total,
        unique_actors=unique_actors,
        actor_counts=actor_counts,
        result_counts=result_counts,
        seeds=tuple(seeds),
        latest_time=latest_time,
    )


def summarize_ledger(
    ledger: "PulseLedger", *, limit: int | None = None
) -> PulseSummary:
    """Summarise activity recorded in *ledger*.

    Parameters
    ----------
    ledger:
        Pulse ledger instance to inspect.
    limit:
        Optional number of most recent receipts to include.  If ``None`` or a
        non-positive integer, the entire ledger is scanned.
    """

    if limit is None or limit <= 0:
        receipts: Sequence["PulseReceipt"] = list(ledger.iter_receipts())
    else:
        receipts = list(ledger.latest(limit=limit))
    return summarize_receipts(receipts)


def render_summary_table(summary: PulseSummary) -> str:
    """Render *summary* as a human-friendly table."""

    if summary.total_receipts == 0:
        return "No pulse receipts were found. Start a new weave to generate activity."

    lines = [
        "Pulse ledger summary",
        f"Total receipts :: {summary.total_receipts}",
        f"Unique actors :: {', '.join(summary.unique_actors) if summary.unique_actors else 'n/a'}",
    ]

    latest = summary.latest_time.isoformat() if summary.latest_time else "n/a"
    lines.append(f"Latest receipt :: {latest}")

    if summary.seeds:
        lines.append(f"Seeds :: {', '.join(summary.seeds)}")
    lines.append("")

    lines.extend(_render_counts("Actors", summary.actor_counts))
    lines.append("")
    lines.extend(_render_counts("Results", summary.result_counts))

    return "\n".join(lines)


def _render_counts(title: str, counts: Mapping[str, int]) -> list[str]:
    lines = [title]
    if not counts:
        lines.append("  (none recorded)")
        return lines

    name_header = "Name"
    count_header = "Count"
    width_name = max(len(name_header), *(len(name) for name in counts.keys()))
    width_count = max(len(count_header), *(len(str(value)) for value in counts.values()))

    lines.append(f"  {name_header.ljust(width_name)} | {count_header.rjust(width_count)}")
    lines.append(f"  {'-' * width_name}-+-{'-' * width_count}")
    for name, value in counts.items():
        lines.append(f"  {name.ljust(width_name)} | {str(value).rjust(width_count)}")
    return lines


def _parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
