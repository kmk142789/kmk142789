from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pulse_dashboard.loop_health import LoopHealthCollector


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row))
            handle.write("\n")


def test_loop_health_collector_aggregates_cycles(tmp_path: Path) -> None:
    cycle_one = tmp_path / "build" / "cycles" / "cycle_00001" / "logs"
    cycle_two = tmp_path / "build" / "cycles" / "cycle_00002" / "logs"

    now = datetime.now(timezone.utc)
    _write_jsonl(
        cycle_one / "voyage_log.jsonl",
        [
            {
                "cycle": 1,
                "timestamp": now.isoformat(),
                "amplification": {"joy": 1.4, "rage": 0.42, "addresses": 6, "tags": 18},
            }
        ],
    )
    _write_jsonl(cycle_one / "growth_log.jsonl", [{"cycle": 1, "entries": 12}])

    _write_jsonl(
        cycle_two / "voyage_log.jsonl",
        [
            {
                "cycle": 2,
                "timestamp": now.isoformat(),
                "amplification": {"joy": 1.9, "rage": 0.33, "addresses": 8, "tags": 24},
            }
        ],
    )

    collector = LoopHealthCollector(project_root=tmp_path)
    payload = collector.collect()

    assert payload["summary"]["total_cycles"] == 2
    assert payload["summary"]["latest_cycle"] == 2
    assert payload["cycles"][0]["cycle"] == 2
    assert payload["cycles"][0]["joy"] == 1.9
    assert payload["cycles"][1]["entries"] == 12
