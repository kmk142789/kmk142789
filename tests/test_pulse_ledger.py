"""Unit tests for :mod:`echo.pulse_ledger`."""

from __future__ import annotations

import json

import pytest

from echo.pulse_ledger import PulseLedger, PulseSnapshot


def test_pulse_ledger_records_and_persists(tmp_path):
    path = tmp_path / "pulse.json"
    ledger = PulseLedger(anchor="Test Anchor", file_path=path)

    entry = ledger.record(
        "drone_funds_allocation",
        resonance="Eden88",
        priority="high",
        data={"amount": "500"},
    )

    assert entry.name == "drone_funds_allocation"
    assert entry.resonance == "Eden88"
    assert entry.priority == "high"
    assert path.exists()

    payload = json.loads(path.read_text())
    assert payload["anchor"] == "Test Anchor"
    assert len(payload["history"]) == 1
    assert payload["history"][0]["data"] == {"amount": "500"}


def test_pulse_ledger_snapshot_returns_latest_entry(tmp_path):
    path = tmp_path / "ledger.json"
    ledger = PulseLedger(file_path=path)
    ledger.record("mirror_merge", priority="critical")

    snapshot = ledger.snapshot()
    assert isinstance(snapshot, PulseSnapshot)
    assert snapshot.anchor == "Our Forever Love"
    assert snapshot.total_pulses == 1
    assert snapshot.last_pulse is not None
    assert snapshot.last_pulse.name == "mirror_merge"


def test_pulse_ledger_recovers_from_invalid_json(tmp_path):
    path = tmp_path / "pulse.json"
    path.write_text("{not valid JSON}")

    ledger = PulseLedger(file_path=path, anchor="Recovered Anchor")
    assert ledger.history == ()

    ledger.record("eden88_sync", resonance="Eden88", priority="critical")
    payload = json.loads(path.read_text())
    assert payload["anchor"] == "Recovered Anchor"
    assert len(payload["history"]) == 1


def test_record_requires_name(tmp_path):
    ledger = PulseLedger(file_path=tmp_path / "pulse.json")
    with pytest.raises(ValueError):
        ledger.record("")

