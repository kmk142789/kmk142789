from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from echo.revolutionary_flux import RevolutionaryFlux


@pytest.fixture()
def sequenced_time_source():
    base = datetime(2035, 5, 11, 12, 0, tzinfo=timezone.utc)

    def _next_time() -> datetime:
        nonlocal base
        current = base
        base = base + timedelta(seconds=1)
        return current

    return _next_time


def test_manifest_tracks_vectors_and_ledger(sequenced_time_source):
    flux = RevolutionaryFlux(time_source=sequenced_time_source)
    vector = flux.register_vector("aurora", glyph="∇", amplitude=2.0)
    assert vector.energy() == pytest.approx(2.0)

    flux.infuse("aurora", source="lattice", delta=1.25, narrative="phase lift")
    signature_after_infuse = flux.orbital_signature()

    flux.stabilise("aurora", new_amplitude=3.5)
    signature_after_stabilise = flux.orbital_signature()
    assert signature_after_stabilise != signature_after_infuse

    manifest = flux.manifest()
    assert manifest["anchor"] == "Our Forever Love"
    assert manifest["vectors"][0]["name"] == "aurora"
    assert manifest["vectors"][0]["energy"] == pytest.approx(vector.energy())
    assert len(manifest["ledger"]) == 3
    assert manifest["ledger"][0]["narrative"] == "Vector registered"
    assert manifest["ledger"][-1]["narrative"] == "Amplitude stabilised"


def test_registering_duplicate_vector_is_blocked(sequenced_time_source):
    flux = RevolutionaryFlux(time_source=sequenced_time_source)
    flux.register_vector("aurora", glyph="∇")
    with pytest.raises(ValueError):
        flux.register_vector("aurora", glyph="⊸")


def test_ledger_limit_truncates_entries(sequenced_time_source):
    flux = RevolutionaryFlux(time_source=sequenced_time_source)
    flux.register_vector("aurora", glyph="∇")
    flux.infuse("aurora", source="bridge", delta=0.5)
    flux.infuse("aurora", source="bridge", delta=0.25)

    limited = flux.manifest(ledger_limit=2)
    assert len(limited["ledger"]) == 2
    assert limited["ledger"][0]["narrative"] == "Infusion applied"
