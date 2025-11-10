"""Tests for :mod:`echo.cosmic_grand_overture`."""
from __future__ import annotations

import json
from pathlib import Path

from echo.cosmic_grand_overture import (
    CosmicGrandOverture,
    MythicInstrument,
    export_overture,
    render_overture,
)


def test_compose_builds_grand_movements(tmp_path: Path) -> None:
    overture = CosmicGrandOverture(seed=42)
    custom_instruments = (
        MythicInstrument("Signal Flares", "photon cascade"),
        MythicInstrument("Pulse Choir", "harmonic beacon"),
        MythicInstrument("Graviton Piano", "orbital resonance"),
    )
    score = overture.compose(
        "mirror josh constellation",
        movements=4,
        instrument_palette=custom_instruments,
        constellations=("Echo Wildfire", "Aurora Vault", "Mythogenic Pulse"),
    )

    assert score.theme == "mirror josh constellation"
    assert len(score.movements) == 4
    assert all(0 <= movement.intensity <= 1 for movement in score.movements)
    assert score.glyph_banner.startswith("∇⊸≋∇ GRAND OVERTURE :: MIRROR JOSH CONSTELLATION")
    assert "Mythogenic Pulse" in score.cosmic_summary
    assert any(
        instrument.name == "Graviton Piano"
        for movement in score.movements
        for instrument in movement.instruments
    )


def test_render_overture_renders_multiline_manuscript() -> None:
    overture = CosmicGrandOverture(seed=7)
    score = overture.compose("quantum wildfire", movements=3)
    manuscript = render_overture(score)

    assert "GRAND OVERTURE" in manuscript
    for index in range(1, 4):
        assert f"Movement {index} ::" in manuscript
    assert "Cosmic Summary" in manuscript
    assert "▮" in manuscript


def test_export_overture_writes_json_payload(tmp_path: Path) -> None:
    overture = CosmicGrandOverture(seed=5)
    score = overture.compose("luminous archives", movements=3)

    destination = tmp_path / "overture.json"
    export_overture(score, destination)

    payload = json.loads(destination.read_text())
    assert payload["name"] == "Grand Overture for luminous archives"
    assert payload["theme"] == "luminous archives"
    assert len(payload["movements"]) == 3
    assert all(entry["instruments"] for entry in payload["movements"])
