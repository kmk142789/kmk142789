from __future__ import annotations

import json
from pathlib import Path

import pytest

from pulse_dashboard.builder import PulseDashboardBuilder


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pulse_dashboard"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _load_fixture(name: str) -> Path:
    return FIXTURE_DIR / name


def test_builder_collects_signals(tmp_path: Path) -> None:
    pulse_history = json.loads(_load_fixture("pulse_history.json").read_text(encoding="utf-8"))
    _write_json(tmp_path / "pulse_history.json", pulse_history)

    attestations_dir = tmp_path / "attestations"
    attestations_dir.mkdir()
    att_payload = json.loads(_load_fixture("attestation_sample.json").read_text(encoding="utf-8"))
    _write_json(attestations_dir / "att-001.json", att_payload)

    dns_fixture = _load_fixture("dns_tokens.txt").read_text(encoding="utf-8")
    (tmp_path / "dns_tokens.txt").write_text(dns_fixture, encoding="utf-8")

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

    amplify_log = tmp_path / "state" / "amplify_log.jsonl"
    amplify_log.parent.mkdir(parents=True, exist_ok=True)
    amplify_log.write_text(_load_fixture("amplify_log.jsonl").read_text(encoding="utf-8"), encoding="utf-8")

    proof_dir = tmp_path / "pulse_dashboard" / "data"
    proof_dir.mkdir(parents=True, exist_ok=True)
    proof_payload = json.loads(_load_fixture("proof_of_computation.json").read_text(encoding="utf-8"))
    _write_json(proof_dir / "proof_of_computation.json", proof_payload)

    builder = PulseDashboardBuilder(project_root=tmp_path)
    payload = builder.build()

    assert payload["pulses"]
    assert payload["attestations"][0]["id"] == "att-001"
    assert payload["dns_snapshots"] == [
        {"domain": "example.com", "token": "token-alpha"},
        {"domain": "echo.example.org", "token": "token-beta"},
    ]
    assert payload["worker_hive"]["total"] == 2
    assert payload["glyph_cycle"]["energy"] > 0
    summary = payload["pulse_summary"]
    assert summary["total"] == len(pulse_history)
    assert summary["latest"]["message"] == payload["pulses"][0]["message"]
    category_names = {item["name"] for item in summary["categories"]}
    assert {"merge", "evolve", "ascend"}.issubset(category_names)
    assert summary["average_wave"] > 0
    total_share = sum(item["share"] for item in summary["categories"])
    assert total_share == pytest.approx(1.0, rel=1e-3)
    assert payload["impact_explorer"]["financials"]["totals"]["donations"] == 0.0
    amplify = payload["amplify"]
    assert amplify["summary"]["cycles_tracked"] == 3
    assert "cycle 2" in amplify["summary"]["presence"]
    assert amplify["latest"]["metrics"]["cohesion"] == 88.5
    proof = payload["proof_of_computation"]
    assert proof["total"] == 2
    assert proof["latest"]["puzzle"] == 22


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


def test_signal_health_summary(tmp_path: Path) -> None:
    pulse_history = json.loads(_load_fixture("pulse_history.json").read_text(encoding="utf-8"))
    _write_json(tmp_path / "pulse_history.json", pulse_history)

    attestations_dir = tmp_path / "attestations"
    attestations_dir.mkdir()
    att_payload = json.loads(_load_fixture("attestation_sample.json").read_text(encoding="utf-8"))
    _write_json(attestations_dir / "att-001.json", att_payload)

    amplify_log = tmp_path / "state" / "amplify_log.jsonl"
    amplify_log.parent.mkdir(parents=True, exist_ok=True)
    amplify_log.write_text(_load_fixture("amplify_log.jsonl").read_text(encoding="utf-8"), encoding="utf-8")

    builder = PulseDashboardBuilder(project_root=tmp_path)
    health = builder.build()["signal_health"]

    assert health["status"] == "vibrant"
    assert health["health_score"] == pytest.approx(75.63, rel=1e-3)
    metrics = health["metrics"]
    assert metrics["average_pulse_gap_seconds"] == 150.0
    assert metrics["pulse_span_seconds"] == 300.0
    assert metrics["attestation_total"] == 1
    assert metrics["amplify_trend"] == "rising"
    assert len(health["insights"]) >= 3
