from __future__ import annotations

import json
from pathlib import Path

from pulse_weaver.schema import validate_snapshot
from pulse_weaver.service import PulseWeaverService


def _write_history(path: Path) -> None:
    history = [
        {"timestamp": 1.0, "message": "cycle-start", "hash": "aaa"},
        {"timestamp": 2.0, "message": "cycle-end", "hash": "bbb"},
    ]
    path.write_text(json.dumps(history), encoding="utf-8")


def test_service_records_and_snapshot(tmp_path: Path) -> None:
    _write_history(tmp_path / "pulse_history.json")
    service = PulseWeaverService(tmp_path)
    service.record_failure(
        key="key-1",
        message="unit test failure",
        proof="proof-1",
        echo="echo-1",
        cycle="cycle-001",
        metadata={"reason": "timeout"},
        atlas_node="Atlas::NodeA",
        phantom_trace="phantom-1",
    )
    service.record_success(
        key="key-2",
        message="unit test success",
        proof="success-proof",
        echo="echo-2",
        cycle="cycle-002",
        metadata={"result": "ok"},
        atlas_node="Atlas::NodeA",
    )

    snapshot = service.snapshot(limit=10)
    payload = snapshot.to_dict()
    validate_snapshot(payload)

    assert payload["schema"] == "pulse.weaver/snapshot-v1"
    assert payload["summary"]["total"] == 2
    assert payload["summary"]["by_status"]["failure"] == 1
    assert payload["summary"]["atlas_links"]["Atlas::NodeA"] == 2
    assert any(item["message"] == "cycle-start" for item in payload["phantom"])
    ledger_keys = {entry["key"] for entry in payload["ledger"]}
    assert {"key-1", "key-2"} <= ledger_keys
    success_entry = next(entry for entry in payload["ledger"] if entry["key"] == "key-2")
    assert success_entry["proof"] == "success-proof"
    assert "Pulse Weaver Rhyme" in payload["rhyme"]
    assert "Total: 2" in payload["rhyme"]
    assert payload["glyph_cycle"]["glyph"]
    assert "window" in payload["glyph_cycle"]


def test_cycle_queries_and_filters(tmp_path: Path) -> None:
    service = PulseWeaverService(tmp_path)
    service.record_failure(
        key="key-cycle-a",
        message="cycle failure",
        cycle="cycle-xyz",
        metadata={"attempt": 1},
    )
    service.record_success(
        key="key-cycle-b",
        message="cycle success",
        cycle="cycle-xyz",
    )
    service.record_failure(
        key="key-cycle-b",
        message="retry failed",
        cycle="cycle-xyz",
    )
    service.record_success(
        key="key-other",
        message="outside cycle",
        cycle="cycle-abc",
    )

    latest = service.get_event("key-cycle-b")
    assert latest is not None
    assert latest.message == "retry failed"
    assert latest.status == "failure"

    full_cycle = service.cycle_ledger("cycle-xyz")
    assert [entry.key for entry in full_cycle] == [
        "key-cycle-a",
        "key-cycle-b",
        "key-cycle-b",
    ]

    only_failures = service.cycle_ledger("cycle-xyz", statuses=("failure",))
    assert [entry.status for entry in only_failures] == ["failure", "failure"]

    summary = service.cycle_summary("cycle-xyz")
    assert summary["failure"] == 2
    assert summary["success"] == 1

    glyph_cycle = service.glyph_cycle()
    assert glyph_cycle.glyph
    assert glyph_cycle.window_end > glyph_cycle.window_start
