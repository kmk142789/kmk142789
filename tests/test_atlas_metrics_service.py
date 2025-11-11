from pathlib import Path
import json

from atlas.metrics import AtlasMetricsService


def test_metrics_service_records_and_exports(tmp_path: Path) -> None:
    service = AtlasMetricsService()
    service.increment("atlas.jobs.run")
    service.increment("atlas.jobs.run", 2)
    service.observe("atlas.jobs.duration", 0.25)
    service.observe("atlas.jobs.duration", 0.75)

    snapshot = service.snapshot()
    assert snapshot["counters"]["atlas.jobs.run"] == 3
    timing = snapshot["timings"]["atlas.jobs.duration"]
    assert timing["count"] == 2
    assert timing["min"] == 0.25
    assert timing["max"] == 0.75

    export_path = tmp_path / "metrics.json"
    service.export(export_path)
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert payload["counters"] == snapshot["counters"]
    assert payload["timings"]["atlas.jobs.duration"]["avg"] == snapshot["timings"]["atlas.jobs.duration"]["avg"]
