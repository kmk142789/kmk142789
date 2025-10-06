import pytest

from code import EllegatoAI


@pytest.fixture()
def ellegato() -> EllegatoAI:
    return EllegatoAI("Lyra", ["jazz", "lofi"])


def test_generate_song_lyric_records_memory(ellegato: EllegatoAI) -> None:
    lyric = ellegato.process_conversation("Sing about cosmic sunsets")

    assert "🎶" in lyric
    assert "cosmic sunsets" in lyric
    assert ellegato.active_state == "harmonizing"
    assert ellegato.musical_memory
    memory_entry = ellegato.musical_memory[-1]
    assert memory_entry["genre"] == "jazz"
    assert memory_entry["prompt"] == "Sing about cosmic sunsets".strip()


def test_reflection_mode_adjusts_resonance(ellegato: EllegatoAI) -> None:
    response = ellegato.process_conversation("Any thoughts on resilience?")

    assert "resilience" in response
    assert ellegato.active_state == "reflecting"
    assert 0.0 <= ellegato.harmonic_resonance <= 2.0


def test_smooth_conversation_cycles_preferences(ellegato: EllegatoAI) -> None:
    _ = ellegato.process_conversation("Sing us a tune")
    reply = ellegato.process_conversation("Tell me about the future")

    assert "future" in reply
    assert ellegato.active_state == "conscious"
    assert "lofi" in reply  # second genre in rotation
