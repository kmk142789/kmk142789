from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

import pytest

from echo.groundbreaking_nexus import (
    GroundbreakingNexus,
    NexusImprint,
    SingularityThread,
    synthesize_breakthrough,
)


def _time_generator(start: datetime, *, step: timedelta) -> Callable[[], datetime]:
    moments = [start + i * step for i in range(10)]

    def _tick() -> datetime:
        if not moments:
            raise RuntimeError("time generator exhausted")
        return moments.pop(0)

    return _tick


def test_groundbreaking_nexus_manifest_and_breakthrough():
    time_source = _time_generator(
        datetime(2025, 5, 11, 12, 0, tzinfo=timezone.utc), step=timedelta(minutes=3)
    )
    nexus = GroundbreakingNexus(anchor="Our Forever Love", time_source=time_source)

    thread_a = SingularityThread(
        name="EchoWildfire",
        glyph="∇⊸≋",
        intensity=2.5,
        curiosity=1.75,
        metadata={"joy": 0.92},
    )
    thread_b = SingularityThread(
        name="MirrorJosh",
        glyph="⊸≋∞",
        intensity=1.1,
        curiosity=3.05,
    )

    nexus.seed_thread(thread_a)
    nexus.seed_thread(thread_b)

    manifest = nexus.compose_manifest()
    assert manifest["anchor"] == "Our Forever Love"
    assert manifest["orbit_hint"] == "Quantum Groundbreaker"

    # Deterministic breakthrough index ensures reproducible orchestration.
    assert manifest["breakthrough_index"] == pytest.approx(10.501447, rel=1e-9)

    matrix = manifest["glyph_matrix"]
    assert matrix[0][0] == 1.0
    assert matrix[1][1] == 1.0
    assert matrix[0][1] == pytest.approx(0.12837, rel=1e-9)
    assert matrix[1][0] == pytest.approx(0.12837, rel=1e-9)

    ledger = manifest["ledger"]
    assert [entry["thread"] for entry in ledger] == ["EchoWildfire", "MirrorJosh"]
    assert ledger[0]["timestamp"].endswith("+00:00")


def test_groundbreaking_nexus_imprint_roundtrip():
    start = datetime(2025, 5, 11, 14, 0, tzinfo=timezone.utc)
    time_source = _time_generator(start, step=timedelta(minutes=2))
    nexus = GroundbreakingNexus(anchor="Bridge Anchor", time_source=time_source)

    nexus.seed_thread(
        SingularityThread(
            name="Eden88",
            glyph="✶∴✶",
            intensity=3.6,
            curiosity=2.2,
            metadata={"curiosity": 0.95, "stability": 0.61},
        )
    )
    imprint = nexus.imprint(orbit="Orbital Bloom")

    assert isinstance(imprint, NexusImprint)
    payload = imprint.to_dict()
    assert payload["anchor"] == "Bridge Anchor"
    assert payload["orbit"] == "Orbital Bloom"
    assert payload["timestamp"] == (start + timedelta(minutes=2)).isoformat()
    assert payload["breakthrough_index"] == pytest.approx(4.841502, rel=1e-9)
    assert payload["glyph_matrix"] == [[1.0]]
    assert payload["contributions"][0]["metadata"]["curiosity"] == 0.95


def test_synthesize_breakthrough_accepts_mixed_inputs():
    start = datetime(2025, 5, 11, 16, 0, tzinfo=timezone.utc)
    time_source = _time_generator(start, step=timedelta(minutes=1))

    imprint = synthesize_breakthrough(
        [
            ("EchoBridge", "∇⊸", 2.0, 1.0),
            SingularityThread(name="Eden", glyph="≋∇", intensity=1.5, curiosity=2.4),
        ],
        anchor="Nexus Anchor",
        orbit="Satellite TF-QKD",
        time_source=time_source,
    )

    assert imprint.anchor == "Nexus Anchor"
    assert imprint.orbit == "Satellite TF-QKD"
    assert len(imprint.contributions) == 2
    charges = [entry["luminous_charge"] for entry in imprint.contributions]
    assert charges == pytest.approx([4.0, 8.45], rel=1e-9)
    assert imprint.breakthrough_index == pytest.approx(8.416632, rel=1e-9)

