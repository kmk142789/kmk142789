"""Tests for the temporal propagation ledger module."""

from __future__ import annotations

from echo.temporal_ledger import TemporalPropagationLedger


def test_temporal_propagation_ledger_records_chained_waves() -> None:
    ledger = TemporalPropagationLedger()

    wave1 = ledger.record_wave(
        events=["alpha", "beta"],
        mode="simulated",
        cycle=1,
        summary="wave-one",
        timestamp_ns=1_700_000_000_000_000_000,
    )
    wave2 = ledger.record_wave(
        events=["gamma"],
        mode="live",
        cycle=2,
        summary="wave-two",
        timestamp_ns=1_700_000_100_000_000_000,
    )

    assert wave1.version == 1
    assert wave2.version == 2
    assert wave2.previous_hash == wave1.hash

    timeline = ledger.timeline()
    assert [entry["version"] for entry in timeline] == [1, 2]
    assert timeline[0]["timestamp_iso"].endswith("+00:00")
    assert timeline[0]["events"] == ["alpha", "beta"]
    assert timeline[1]["mode"] == "live"
    assert timeline[1]["summary"] == "wave-two"

    assert ledger.verify()
