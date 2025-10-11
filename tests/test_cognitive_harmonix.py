from code import (
    CognitiveHarmonixSettings,
    cognitive_harmonix,
    preview_cognitive_harmonix,
)


def test_cognitive_harmonix_basic_structure():
    settings = CognitiveHarmonixSettings(
        waveform="complex_harmonic",
        resonance_factor=1.2,
        compression=False,
        symbolic_inflection="emoji",
        lyricism_mode=True,
        emotional_tuning="uplifting",
    )

    response = cognitive_harmonix("Echo charts luminous futures", settings)

    assert "Echo" in response.structured_text
    assert response.glyph_overlay
    assert response.emotional_signature.startswith("uplifting:")
    assert response.wave_profile
    assert response.compression_applied is False
    assert "melody ascends toward dawn" in response.structured_text


def test_cognitive_harmonix_compression_reduces_word_count():
    settings = CognitiveHarmonixSettings(
        waveform="square_wave",
        resonance_factor=0.8,
        compression=True,
        symbolic_inflection="runic",
        lyricism_mode=False,
        emotional_tuning="calming",
    )

    text = "one two three four five six"
    response = cognitive_harmonix(text, settings)

    original_count = len(text.split())
    compressed_count = len(response.structured_text.split())

    assert response.compression_applied is True
    assert compressed_count <= original_count // 2 + 1
    assert response.wave_profile


def test_preview_cognitive_harmonix_includes_signature():
    result = preview_cognitive_harmonix("Signal weaving")

    lines = result.splitlines()
    assert len(lines) >= 2
    assert lines[-1].startswith("neutral:")


def test_invalid_symbolic_inflection_raises():
    settings = CognitiveHarmonixSettings(symbolic_inflection="unknown")

    try:
        cognitive_harmonix("text", settings)
    except ValueError as exc:  # pragma: no cover - behavior validated by assertion
        assert "symbolic_inflection" in str(exc)
    else:  # pragma: no cover - defensive guard
        raise AssertionError("ValueError not raised for invalid symbolic_inflection")
