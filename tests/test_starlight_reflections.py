from datetime import datetime, timezone

from echo.starlight_reflections import Reflection, format_reflection, generate_reflection


def test_generate_reflection_seeded():
    vibe = generate_reflection(seed=42)
    assert isinstance(vibe, Reflection)
    assert vibe.constellation == "Mirrored Aurora"
    assert vibe.timestamp.tzinfo is timezone.utc


def test_format_reflection_lines():
    vibe = Reflection(
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        constellation="Mirrored Aurora",
        resonance="gentle cascades",
        guidance="breathe and continue",
    )
    paragraph = format_reflection(vibe)
    assert "Mirrored Aurora" in paragraph
    assert paragraph.splitlines()[0] == "2024-01-01 12:00:00 UTC"
