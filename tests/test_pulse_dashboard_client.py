from __future__ import annotations

import json
from pathlib import Path

import pytest

from pulse_dashboard.builder import PulseDashboardBuilder
from pulse_dashboard.client import PulseDashboardClient


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pulse_dashboard"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _load_fixture(name: str) -> Path:
    return FIXTURE_DIR / name


def _prepare_dashboard_environment(root: Path) -> Path:
    pulse_history = json.loads(_load_fixture("pulse_history.json").read_text(encoding="utf-8"))
    _write_json(root / "pulse_history.json", pulse_history)

    attestations_dir = root / "attestations"
    attestations_dir.mkdir()
    att_payload = json.loads(_load_fixture("attestation_sample.json").read_text(encoding="utf-8"))
    _write_json(attestations_dir / "att-001.json", att_payload)

    dns_fixture = _load_fixture("dns_tokens.txt").read_text(encoding="utf-8")
    (root / "dns_tokens.txt").write_text(dns_fixture, encoding="utf-8")

    worker_state = root / "state" / "pulse_dashboard"
    worker_state.mkdir(parents=True)
    worker_log = worker_state / "worker_events.jsonl"
    worker_log.write_text(
        "\n".join(
            [
                json.dumps({"status": "start", "name": "verify", "timestamp": "2025-01-01T00:00:00Z"}),
                json.dumps(
                    {
                        "status": "success",
                        "name": "verify",
                        "payload": {"checked": 42},
                        "timestamp": "2025-01-01T00:00:10Z",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    amplify_log = root / "state" / "amplify_log.jsonl"
    amplify_log.parent.mkdir(parents=True, exist_ok=True)
    amplify_log.write_text(_load_fixture("amplify_log.jsonl").read_text(encoding="utf-8"), encoding="utf-8")

    proof_dir = root / "pulse_dashboard" / "data"
    proof_dir.mkdir(parents=True, exist_ok=True)
    proof_payload = json.loads(_load_fixture("proof_of_computation.json").read_text(encoding="utf-8"))
    _write_json(proof_dir / "proof_of_computation.json", proof_payload)

    builder = PulseDashboardBuilder(project_root=root)
    return builder.write()


@pytest.fixture()
def dashboard_client(tmp_path: Path) -> PulseDashboardClient:
    dashboard_path = _prepare_dashboard_environment(tmp_path)
    return PulseDashboardClient.from_file(dashboard_path)


def test_client_summarises_dashboard(dashboard_client: PulseDashboardClient) -> None:
    assert dashboard_client.total_pulses() == 3
    categories = dashboard_client.pulse_categories()
    assert len(categories) == 3
    assert {name for name, _ in categories} == {"merge", "evolve", "ascend"}
    latest = dashboard_client.latest_pulse_message()
    assert latest is not None
    assert latest.startswith("🚀 ascend")
    assert dashboard_client.average_pulse_wave() > 0
    assert dashboard_client.amplify_momentum() == pytest.approx(5.25)
    assert dashboard_client.glyph_energy() > 0
    assert dashboard_client.attestation_ids() == ["att-001"]
    assert dashboard_client.proof_count() == 2
    presence = dashboard_client.amplify_presence_message()
    assert presence is not None
    assert presence.startswith("Amplify presence cycle")
    activity = dashboard_client.pulse_activity_report()
    assert activity.startswith("Pulse activity :: Pulses tracked")
    evolution = dashboard_client.loop_evolution_status()
    assert evolution.startswith("Loop evolution ::")


def test_client_history_helpers(dashboard_client: PulseDashboardClient) -> None:
    history = dashboard_client.amplify_history(limit=2)
    assert len(history) == 2
    assert history[0]["cycle"] == 2
    events = dashboard_client.recent_worker_events()
    assert len(events) == 2
    summary = dashboard_client.describe()
    assert "Pulse Dashboard" in summary
    assert "Glyph energy" in summary
    assert "Latest pulse" in summary
    assert "Amplify presence:" in summary
    assert "Loop evolution" in summary
