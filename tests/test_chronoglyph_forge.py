import pytest

from src.chronoglyph_forge import ChronoglyphForge


def test_chronoglyph_determinism():
    forge = ChronoglyphForge(seed=99)
    events = ["orbital garden", "luminous data", "tidal archive"]
    timestamp = 1_700_000_000.0

    glyph_one = forge.forge(events, "terraform joy", timestamp=timestamp)
    glyph_two = forge.forge(events, "terraform joy", timestamp=timestamp)

    assert glyph_one.signature == glyph_two.signature
    assert glyph_one.temporal_lattice == glyph_two.temporal_lattice
    assert glyph_one.phase_braid == glyph_two.phase_braid


def test_chronoglyph_expected_waveform():
    forge = ChronoglyphForge(seed=7)
    timestamp = 1_699_999_999.123
    glyph = forge.forge(["aurora", "skyway"], "signal lantern", timestamp=timestamp)

    assert glyph.prime_backbone == [2, 3]
    assert glyph.temporal_lattice == [-0.442784, -0.751523]
    assert glyph.signature == "CG-3d6bbb44f25a85d7fdb343c8"
    assert "Harmonic clock" in glyph.narrative
    assert "Phase braid" in glyph.narrative


@pytest.mark.parametrize("events", [[], ["   "]])
def test_chronoglyph_rejects_empty(events):
    forge = ChronoglyphForge(seed=3)
    with pytest.raises(ValueError):
        forge.forge(events, "intent", timestamp=0.0)
