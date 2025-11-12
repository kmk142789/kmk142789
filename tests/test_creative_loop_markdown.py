"""Tests for the Markdown output option in :mod:`src.creative_loop`."""

from __future__ import annotations

from src.creative_loop import LoopSeed, compose_loop


def test_markdown_format_structure() -> None:
    """Markdown output should include headings, bullets, and metadata."""

    seed = LoopSeed(
        motif="aurora",
        fragments=("horizon", "echo"),
        tempo="andante",
        pulses=2,
        seed=7,
    )

    markdown = compose_loop(seed, format="markdown")
    lines = markdown.splitlines()

    assert lines[0] == "## Loop for 'aurora'"
    assert lines[1].startswith("*Composed ")
    assert lines[3].startswith("- ")
    assert lines[4].startswith("- ")
    assert lines[-2].startswith("> Diagnostics: Voices[")
    assert lines[-1].startswith("> Rhythm: tempo=andante; pulses=2; accents=")
