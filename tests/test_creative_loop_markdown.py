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
    assert any(line.startswith("> Diagnostics: Voices[") for line in lines)
    assert any(line.startswith("> Summary: diversity=") for line in lines)
    assert any(line.startswith("> Fingerprint: ") for line in lines)
    assert any(
        line.startswith("> Rhythm: tempo=andante; pulses=2; accents=") for line in lines
    )
