from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pulse_dashboard.builder import PulseDashboardBuilder


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_builder_collects_signals(tmp_path: Path) -> None:
    pulse_history = [
        {"timestamp": 1_700_000_000, "message": "🌊 merge:codex", "hash": "abc123"},
        {"timestamp": 1_700_000_100, "message": "🛠 evolve:worker", "hash": "def456"},
    ]
    _write_json(tmp_path / "pulse_history.json", pulse_history)

    attestations_dir = tmp_path / "attestations"
    attestations_dir.mkdir()
    _write_json(
        attestations_dir / "att-001.json",
        {
            "message": "Sample attestation",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "hash_sha256": "deadbeef",
            "puzzle": "#001",
        },
    )

    (tmp_path / "dns_tokens.txt").write_text("example.com=token", encoding="utf-8")

    worker_state = tmp_path / "state" / "pulse_dashboard"
    worker_state.mkdir(parents=True)
    worker_log = worker_state / "worker_events.jsonl"
    worker_log.write_text(
        "\n".join(
            [
                json.dumps({"status": "start", "name": "verify", "timestamp": "2025-01-01T00:00:00Z"}),
                json.dumps({
                    "status": "success",
                    "name": "verify",
                    "payload": {"checked": 42},
                    "timestamp": "2025-01-01T00:00:10Z",
                }),
            ]
        ),
        encoding="utf-8",
    )

    builder = PulseDashboardBuilder(project_root=tmp_path)
    payload = builder.build()

    assert payload["pulses"]
    assert payload["attestations"][0]["id"] == "att-001"
    assert payload["dns_snapshots"] == [{"domain": "example.com", "token": "token"}]
    assert payload["worker_hive"]["total"] == 2
    assert payload["glyph_cycle"]["energy"] > 0


@pytest.mark.parametrize(
    "message, expected",
    [
        ("🌊 merge:codex", "merge"),
        ("🚀 ascend", "ascend"),
        ("unknown", "unknown"),
    ],
)
def test_pulse_classification(tmp_path: Path, message: str, expected: str) -> None:
    _write_json(
        tmp_path / "pulse_history.json",
        [{"timestamp": 1_700_000_000, "message": message, "hash": "abc"}],
    )
    builder = PulseDashboardBuilder(project_root=tmp_path)
    pulses = builder.build()["pulses"]
    assert pulses[0]["category"] == expected
