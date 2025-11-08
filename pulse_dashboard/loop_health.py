"""Collect cycle loop metrics for the Pulse dashboard."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


@dataclass(slots=True)
class LoopHealthPaths:
    """Filesystem locations used by the loop health collector."""

    root: Path

    @property
    def cycles_dir(self) -> Path:
        return self.root / "build" / "cycles"


class LoopHealthCollector:
    """Aggregate orchestrator loop telemetry into dashboard friendly data."""

    def __init__(self, project_root: Path | str | None = None) -> None:
        self._paths = LoopHealthPaths(root=Path(project_root or Path.cwd()).resolve())

    # ------------------------------------------------------------------
    # Public API

    def collect(self) -> dict[str, Any]:
        """Return loop health metrics derived from orchestration logs."""

        cycles = [
            payload
            for payload in (
                self._load_cycle(directory)
                for directory in sorted(self._paths.cycles_dir.glob("cycle_*"))
            )
            if payload is not None
        ]
        cycles.sort(key=lambda item: item["cycle"], reverse=True)

        summary = self._summarise(cycles)
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "cycles": cycles,
            "summary": summary,
        }

    # ------------------------------------------------------------------
    # Internal helpers

    def _load_cycle(self, directory: Path) -> dict[str, Any] | None:
        logs_dir = directory / "logs"
        if not logs_dir.exists():
            return None

        voyage = self._latest_json_line(logs_dir / "voyage_log.jsonl")
        growth = self._latest_json_line(logs_dir / "growth_log.jsonl")
        if not voyage and not growth:
            return None

        cycle = self._coerce_cycle(directory, voyage, growth)
        payload: dict[str, Any] = {"cycle": cycle}

        if voyage:
            amplification = voyage.get("amplification", {})
            payload["joy"] = float(amplification.get("joy", 0.0))
            payload["rage"] = float(amplification.get("rage", 0.0))
            payload["addresses"] = float(amplification.get("addresses", 0.0))
            payload["tags"] = float(amplification.get("tags", 0.0))
            payload["recorded_at"] = voyage.get("timestamp")
        if growth:
            payload["entries"] = int(growth.get("entries", 0))
            payload.setdefault("recorded_at", growth.get("timestamp"))

        return payload

    @staticmethod
    def _coerce_cycle(directory: Path, *records: dict[str, Any] | None) -> int:
        for record in records:
            if record and "cycle" in record:
                try:
                    return int(record["cycle"])
                except (TypeError, ValueError):  # pragma: no cover - defensive
                    continue
        stem = directory.name
        try:
            return int(stem.split("_")[-1])
        except ValueError:  # pragma: no cover - defensive
            return 0

    @staticmethod
    def _latest_json_line(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            lines = path.read_text(encoding="utf-8").strip().splitlines()
        except OSError:  # pragma: no cover - defensive
            return None
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
        return None

    @staticmethod
    def _summarise(cycles: Iterable[dict[str, Any]]) -> dict[str, Any]:
        snapshot = list(cycles)
        if not snapshot:
            return {
                "total_cycles": 0,
                "latest_cycle": None,
                "average_joy": 0.0,
                "average_rage": 0.0,
            }

        total = len(snapshot)
        joy_values = [item.get("joy", 0.0) for item in snapshot]
        rage_values = [item.get("rage", 0.0) for item in snapshot]
        return {
            "total_cycles": total,
            "latest_cycle": snapshot[0]["cycle"],
            "average_joy": sum(joy_values) / total if total else 0.0,
            "average_rage": sum(rage_values) / total if total else 0.0,
        }


__all__ = ["LoopHealthCollector"]
