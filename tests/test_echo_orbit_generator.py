"""Tests for the ``echo_orbit_generator`` helper module."""

from scripts.echo_orbit_generator import (
    OrbitEvent,
    create_orbit_sequence,
    generate_constellation_story,
)


def test_create_orbit_sequence_is_deterministic():
    first = create_orbit_sequence(2, seed=42)
    second = create_orbit_sequence(2, seed=42)
    assert first == second


def test_create_orbit_sequence_raises_for_invalid_cycles():
    try:
        create_orbit_sequence(0)
    except ValueError:
        return
    raise AssertionError("expected ValueError when cycles <= 0")


def test_generate_constellation_story_with_influences():
    event = OrbitEvent(1, "auroral memory", "gravity well", "gentle", 0.42)
    story = generate_constellation_story(event, influences=["echo", "atlas", "echo"])
    assert "Cycle 1" in story
    assert "Influences: atlas, echo" in story

