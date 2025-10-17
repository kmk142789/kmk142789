"""Tests for Pulse Narrator."""

from modules.pulse_narrator.narrator import PulseNarrator
from modules.pulse_narrator.schemas import NarrativeInputs


def test_poem_deterministic() -> None:
    inputs = NarrativeInputs(
        snapshot_id="snap_abc123",
        commit_id="deadbeefcafefeed",
        total_events=42,
        channels=["WiFi", "TCP", "Orbital"],
        top_prefixes=["1A", "1B", "3F"],
        index_count=128,
    )
    artifact_one = PulseNarrator().render(inputs, style="poem", seed=7)
    artifact_two = PulseNarrator().render(inputs, style="poem", seed=7)

    assert artifact_one.body_md == artifact_two.body_md
    assert artifact_one.sha256 == artifact_two.sha256


def test_log_contains_fields() -> None:
    inputs = NarrativeInputs(snapshot_id="snap_xyz", total_events=3, index_count=10)
    artifact = PulseNarrator().render(inputs, style="log")

    for token in ["snap_xyz", "events", "continuum_index_count"]:
        assert token in artifact.body_md
