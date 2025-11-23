from echo.tools.resonance_index import compute_resonance_fingerprint


def test_resonance_fingerprint_empty_series():
    fingerprint = compute_resonance_fingerprint([])

    assert fingerprint.glyph == "⌀"
    assert fingerprint.signature == "0" * 12
    assert fingerprint.coherence == 0.0
    assert fingerprint.rarity == 0.0


def test_resonance_fingerprint_monotonic_growth():
    fingerprint = compute_resonance_fingerprint([1, 2, 3, 4, 5])

    assert fingerprint.baseline == 5.0
    assert fingerprint.velocity == 1.0
    assert fingerprint.inversion_points == 0
    assert fingerprint.glyph == "⌖⟁⟁"
    assert fingerprint.signature == "ddd7b648e841"
    assert 0.55 <= fingerprint.coherence <= 0.56
    assert round(fingerprint.rarity, 4) == 0.0909


def test_resonance_fingerprint_inversion_rich_series():
    fingerprint = compute_resonance_fingerprint([1, 3, 0, 4, -2], window=4, label="test")

    assert fingerprint.inversion_points == 2
    assert fingerprint.glyph == "⌖⌖✶"
    assert fingerprint.signature == "47fdff1cc31b"
    assert fingerprint.coherence == 0.25
    assert round(fingerprint.rarity, 4) == 0.3511
