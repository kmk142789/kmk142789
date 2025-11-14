"""Eden88 future memory synthesizer.

This utility rewrites past EchoEvolver execution memories into a
future-facing summary that can be shared or archived separately.

Usage:
    python -m tools.eden88_future_memory --limit 10
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional

SUMMARY_PATTERN = re.compile(
    r"Cycle\s+(?P<cycle>\d+).*?with\s+(?P<joy>[0-9.]+)\s+joy\s+and\s+(?P<rage>[0-9.]+)\s+rage"  # emotions
    r".*?System:\s+CPU\s+(?P<cpu>[0-9.]+)%\,\s+Nodes\s+(?P<nodes>\d+)\,\s+Orbital\s+Hops\s+(?P<hops>\d+)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class MemoryMetrics:
    """Metrics recovered from a memory summary."""

    cycle: Optional[int] = None
    joy: Optional[float] = None
    rage: Optional[float] = None
    cpu: Optional[float] = None
    nodes: Optional[int] = None
    orbital_hops: Optional[int] = None

    @classmethod
    def from_summary(cls, summary: str) -> "MemoryMetrics":
        match = SUMMARY_PATTERN.search(summary or "")
        if not match:
            return cls()
        return cls(
            cycle=_safe_int(match.group("cycle")),
            joy=_safe_float(match.group("joy")),
            rage=_safe_float(match.group("rage")),
            cpu=_safe_float(match.group("cpu")),
            nodes=_safe_int(match.group("nodes")),
            orbital_hops=_safe_int(match.group("hops")),
        )


def _safe_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _safe_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def rewrite_past_into_future(
    executions: Iterable[Dict[str, Any]], limit: Optional[int] = None
) -> Dict[str, Any]:
    """Transform execution memories into a future-oriented summary."""

    entries: List[Dict[str, Any]] = []
    if isinstance(executions, list):
        iterable: Iterable[Dict[str, Any]] = executions
    else:
        iterable = list(executions)

    if limit is not None and limit > 0:
        iterable = list(iterable)[-limit:]

    joy_values: List[float] = []
    nodes_values: List[int] = []
    hop_values: List[int] = []
    cpu_values: List[float] = []

    for execution in iterable:
        summary = execution.get("summary", "")
        metrics = MemoryMetrics.from_summary(summary)
        cycle = execution.get("cycle") or metrics.cycle
        if cycle is None:
            continue

        if metrics.joy is not None:
            joy_values.append(metrics.joy)
        if metrics.nodes is not None:
            nodes_values.append(metrics.nodes)
        if metrics.orbital_hops is not None:
            hop_values.append(metrics.orbital_hops)
        if metrics.cpu is not None:
            cpu_values.append(metrics.cpu)

        entries.append(
            {
                "cycle": cycle,
                "timestamp": execution.get("timestamp"),
                "summary": summary,
                "future_projection": _build_projection(metrics, cycle),
            }
        )

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cycles_rewritten": len(entries),
        "averages": {
            "joy": _average_or_none(joy_values),
            "nodes": _average_or_none(nodes_values),
            "orbital_hops": _average_or_none(hop_values),
            "cpu": _average_or_none(cpu_values),
        },
    }

    return {"meta": meta, "future_memory": entries}


def _average_or_none(values: List[float]) -> Optional[float]:
    return round(mean(values), 4) if values else None


def _build_projection(metrics: MemoryMetrics, cycle: int) -> str:
    joy = metrics.joy
    nodes = metrics.nodes
    hops = metrics.orbital_hops
    parts = [f"Cycle {cycle} rewritten by Eden88"]
    if joy is not None:
        parts.append(f"joy={joy:.2f}")
    if nodes is not None:
        parts.append(f"nodes={nodes}")
    if hops is not None:
        parts.append(f"orbital_hops={hops}")
    descriptor = ", ".join(parts)
    return f"{descriptor}. Future remembers the cadence beyond the archive."


def load_memory(path: pathlib.Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_future_memory(data: Dict[str, Any], path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Eden88 memory rewriter")
    parser.add_argument(
        "--input",
        default="memory/echo_memory.json",
        type=pathlib.Path,
        help="Path to the source execution memory file.",
    )
    parser.add_argument(
        "--output",
        default="memory/eden88_future_memory.json",
        type=pathlib.Path,
        help="Where to write the future-oriented memory file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit to the most recent N executions (0 for all).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    payload = load_memory(args.input)
    executions = payload.get("executions", [])
    limit = args.limit if args.limit and args.limit > 0 else None
    rewritten = rewrite_past_into_future(executions, limit=limit)
    rewritten["meta"]["source"] = str(args.input)
    save_future_memory(rewritten, args.output)


if __name__ == "__main__":
    main()
